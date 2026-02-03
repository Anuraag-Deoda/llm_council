"""
Conflict detection service for identifying contradictions between sources.

Uses LLM-based pairwise comparison to detect various types of conflicts:
- Factual: Contradictory facts
- Temporal: Outdated vs newer information
- Opinion: Differing opinions/interpretations
- Numerical: Conflicting numbers/statistics
- Procedural: Different processes/steps
"""
import logging
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import asyncio

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.database.rag_models import ConflictRecord, ConflictType, ConflictStatus
from .trust_scorer import ScoredChunk

logger = logging.getLogger(__name__)


@dataclass
class DetectedConflict:
    """Represents a detected conflict between two chunks."""
    chunk_a_id: int
    chunk_b_id: int
    chunk_a_content: str
    chunk_b_content: str
    chunk_a_source: str
    chunk_b_source: str
    chunk_a_author: Optional[str]
    chunk_b_author: Optional[str]
    conflict_type: ConflictType
    confidence: float
    explanation: str
    recommendation: str


CONFLICT_DETECTION_PROMPT = """You are an expert at analyzing text for contradictions and conflicts.

Given two text passages from different sources, analyze if they contain any conflicting information.

Passage A (from {source_a}):
{content_a}

Passage B (from {source_b}):
{content_b}

Analyze these passages and determine if there is a conflict. Consider these conflict types:
- factual: Direct contradiction of facts (e.g., "The API supports 100 requests" vs "The API supports 500 requests")
- temporal: Information that may be outdated vs newer (e.g., old documentation vs recent announcement)
- opinion: Different interpretations or opinions on the same topic
- numerical: Conflicting numbers, statistics, or quantitative data
- procedural: Different steps or processes for the same task

Respond in JSON format:
{{
    "has_conflict": true/false,
    "conflict_type": "factual|temporal|opinion|numerical|procedural|none",
    "confidence": 0.0-1.0,
    "explanation": "Brief explanation of the conflict",
    "recommendation": "Suggestion for resolving or handling the conflict"
}}

If there is no conflict, set has_conflict to false and leave other fields as appropriate defaults.
Be conservative - only flag genuine contradictions, not complementary information.
"""


class ConflictDetector:
    """
    Service for detecting conflicts between retrieved document chunks.

    Uses an LLM to perform pairwise comparison of chunks and
    identify various types of contradictions.
    """

    def __init__(
        self,
        model: str = None,
        confidence_threshold: float = None,
        max_comparisons: int = None,
        api_key: str = None,
    ):
        """
        Initialize the conflict detector.

        Args:
            model: LLM model for conflict detection
            confidence_threshold: Minimum confidence to report conflict
            max_comparisons: Maximum number of pairwise comparisons
            api_key: OpenAI API key
        """
        self.model = model or settings.rag_conflict_model
        self.confidence_threshold = confidence_threshold or settings.rag_conflict_threshold
        self.max_comparisons = max_comparisons or 10  # n*(n-1)/2 for top 5
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def detect_conflicts(
        self,
        chunks: List[ScoredChunk],
        top_n: int = None,
    ) -> List[DetectedConflict]:
        """
        Detect conflicts among top retrieved chunks.

        Args:
            chunks: List of scored chunks to check
            top_n: Number of top chunks to check (default from settings)

        Returns:
            List of detected conflicts
        """
        top_n = top_n or settings.rag_conflict_check_top_n
        chunks_to_check = chunks[:top_n]

        if len(chunks_to_check) < 2:
            return []

        # Generate all pairs for comparison
        pairs = []
        for i, chunk_a in enumerate(chunks_to_check):
            for chunk_b in chunks_to_check[i+1:]:
                # Skip comparing chunks from same document
                if chunk_a.document_id == chunk_b.document_id:
                    continue
                pairs.append((chunk_a, chunk_b))

        if not pairs:
            return []

        # Limit comparisons
        pairs = pairs[:self.max_comparisons]

        # Run comparisons in parallel
        tasks = [
            self._compare_pair(chunk_a, chunk_b)
            for chunk_a, chunk_b in pairs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect conflicts that meet threshold
        conflicts = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Conflict detection failed: {result}")
                continue
            if result and result.confidence >= self.confidence_threshold:
                conflicts.append(result)

        return conflicts

    async def _compare_pair(
        self,
        chunk_a: ScoredChunk,
        chunk_b: ScoredChunk,
    ) -> Optional[DetectedConflict]:
        """
        Compare two chunks for conflicts.

        Args:
            chunk_a: First chunk
            chunk_b: Second chunk

        Returns:
            DetectedConflict if found, None otherwise
        """
        prompt = CONFLICT_DETECTION_PROMPT.format(
            source_a=f"{chunk_a.source_name} ({chunk_a.document_title})",
            content_a=chunk_a.content[:2000],  # Limit content length
            source_b=f"{chunk_b.source_name} ({chunk_b.document_title})",
            content_b=chunk_b.content[:2000],
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You analyze text for contradictions. Always respond in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)

            if not result.get("has_conflict", False):
                return None

            # Map conflict type
            conflict_type_str = result.get("conflict_type", "factual").lower()
            conflict_type_map = {
                "factual": ConflictType.FACTUAL,
                "temporal": ConflictType.TEMPORAL,
                "opinion": ConflictType.OPINION,
                "numerical": ConflictType.NUMERICAL,
                "procedural": ConflictType.PROCEDURAL,
            }
            conflict_type = conflict_type_map.get(conflict_type_str, ConflictType.FACTUAL)

            return DetectedConflict(
                chunk_a_id=chunk_a.chunk_id,
                chunk_b_id=chunk_b.chunk_id,
                chunk_a_content=chunk_a.content,
                chunk_b_content=chunk_b.content,
                chunk_a_source=chunk_a.source_name,
                chunk_b_source=chunk_b.source_name,
                chunk_a_author=chunk_a.author,
                chunk_b_author=chunk_b.author,
                conflict_type=conflict_type,
                confidence=float(result.get("confidence", 0.5)),
                explanation=result.get("explanation", ""),
                recommendation=result.get("recommendation", "Verify with authoritative source"),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse conflict detection response: {e}")
            return None
        except Exception as e:
            logger.error(f"Conflict detection error: {e}")
            raise

    def save_conflicts(
        self,
        db: Session,
        conflicts: List[DetectedConflict],
        query: str = None,
        retrieval_log_id: int = None,
    ) -> List[int]:
        """
        Save detected conflicts to the database.

        Args:
            db: Database session
            conflicts: List of detected conflicts
            query: Original query that triggered detection
            retrieval_log_id: ID of the retrieval log

        Returns:
            List of created conflict record IDs
        """
        conflict_ids = []

        for conflict in conflicts:
            record = ConflictRecord(
                chunk_a_id=conflict.chunk_a_id,
                chunk_b_id=conflict.chunk_b_id,
                conflict_type=conflict.conflict_type,
                confidence=conflict.confidence,
                explanation=conflict.explanation,
                recommendation=conflict.recommendation,
                status=ConflictStatus.DETECTED,
                query=query,
                retrieval_log_id=retrieval_log_id,
            )
            db.add(record)
            db.flush()
            conflict_ids.append(record.id)

        db.commit()
        return conflict_ids

    def format_conflict_report(
        self,
        conflicts: List[DetectedConflict],
    ) -> str:
        """
        Format conflicts into a human-readable report.

        Args:
            conflicts: List of detected conflicts

        Returns:
            Formatted conflict report string
        """
        if not conflicts:
            return ""

        report_parts = [
            "⚠️ CONFLICTING INFORMATION DETECTED",
            "=" * 50,
        ]

        for i, conflict in enumerate(conflicts, 1):
            report_parts.append(f"\nConflict #{i} ({conflict.conflict_type.value.upper()})")
            report_parts.append(f"Confidence: {conflict.confidence:.0%}")
            report_parts.append("-" * 30)

            report_parts.append(f"\n📄 Source A ({conflict.chunk_a_source}):")
            if conflict.chunk_a_author:
                report_parts.append(f"   Author: {conflict.chunk_a_author}")
            # Truncate content for display
            content_a = conflict.chunk_a_content[:300]
            if len(conflict.chunk_a_content) > 300:
                content_a += "..."
            report_parts.append(f"   \"{content_a}\"")

            report_parts.append(f"\n📄 Source B ({conflict.chunk_b_source}):")
            if conflict.chunk_b_author:
                report_parts.append(f"   Author: {conflict.chunk_b_author}")
            content_b = conflict.chunk_b_content[:300]
            if len(conflict.chunk_b_content) > 300:
                content_b += "..."
            report_parts.append(f"   \"{content_b}\"")

            report_parts.append(f"\n💡 Analysis: {conflict.explanation}")
            report_parts.append(f"📋 Recommendation: {conflict.recommendation}")
            report_parts.append("-" * 30)

        return "\n".join(report_parts)

    def format_conflict_for_prompt(
        self,
        conflicts: List[DetectedConflict],
    ) -> str:
        """
        Format conflicts for inclusion in an LLM prompt.

        Args:
            conflicts: List of detected conflicts

        Returns:
            Formatted string for prompt inclusion
        """
        if not conflicts:
            return ""

        lines = [
            "\n[IMPORTANT: The following conflicts were detected in the source material. "
            "Be sure to acknowledge these discrepancies in your response and suggest "
            "how the user might resolve them.]\n"
        ]

        for conflict in conflicts:
            lines.append(
                f"- {conflict.conflict_type.value.upper()} conflict (confidence: {conflict.confidence:.0%}): "
                f"{conflict.explanation}"
            )
            lines.append(f"  Source A ({conflict.chunk_a_source}): {conflict.chunk_a_content[:150]}...")
            lines.append(f"  Source B ({conflict.chunk_b_source}): {conflict.chunk_b_content[:150]}...")
            lines.append(f"  Recommendation: {conflict.recommendation}")
            lines.append("")

        return "\n".join(lines)
