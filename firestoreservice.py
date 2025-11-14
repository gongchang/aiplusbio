from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

try:
    from google.cloud import firestore
except ImportError:  # pragma: no cover
    firestore = None  # type: ignore


class EventStore:
    """Persist events in Firestore when running in Google Cloud."""

    def __init__(self, collection_name: str = "events") -> None:
        if firestore is None:
            raise RuntimeError(
                "google-cloud-firestore is not installed. Install it or set USE_FIRESTORE=false."
            )

        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        kwargs = {"project": project} if project else {}
        self._client = firestore.Client(**kwargs)
        self._collection = self._client.collection(collection_name)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def upsert_events(self, events: Iterable[Dict]) -> int:
        count = 0
        batch = self._client.batch()

        for event in events:
            doc_id = self._document_id(event)
            payload = self._normalise_event(event)
            batch.set(self._collection.document(doc_id), payload)
            count += 1

        batch.commit()
        return count

    def prune_older_than(self, days: int) -> int:
        cutoff = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        deleted = 0
        for doc in self._collection.where("date", "<", cutoff).stream():
            doc.reference.delete()
            deleted += 1
        return deleted

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    def list_events(self, limit: int = 200, upcoming_only: bool = True) -> List[Dict]:
        query = self._collection.order_by("date")
        if upcoming_only:
            query = query.where("date", ">=", datetime.utcnow().date().isoformat())
        return [doc.to_dict() for doc in query.limit(limit).stream()]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _document_id(event: Dict) -> str:
        date = event.get("date", "none")
        url = event.get("url") or event.get("source_url") or "missing"
        return f"{date}_{abs(hash(url))}"

    @staticmethod
    def _normalise_event(event: Dict) -> Dict:
        return {
            "title": event.get("title", "Untitled Event"),
            "description": event.get("description", ""),
            "date": event.get("date", ""),
            "time": event.get("time", ""),
            "location": event.get("location", ""),
            "url": event.get("url", event.get("source_url", "")),
            "source_url": event.get("source_url", event.get("url", "")),
            "is_virtual": bool(event.get("is_virtual", False)),
            "requires_registration": bool(event.get("requires_registration", False)),
            "categories": event.get("categories", []),
            "institution": event.get("institution", "Others"),
            "updated_at": datetime.utcnow().isoformat(),
        }
