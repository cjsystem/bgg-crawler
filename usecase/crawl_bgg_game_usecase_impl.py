# python
# usecase/service/crawl_bgg_game_usecase_impl.py
from __future__ import annotations

from typing import Dict, Any, List, Set
import logging
import datetime

from usecase.crawl_bgg_game_usecase import CrawlBGGGameUseCase
from usecase.port.bgg_game_parser_service import BGGGameParserService
from usecase.port.games_repository import GamesRepository
from usecase.port.target_games_repository import TargetGamesRepository
from usecase.port.crawl_repository import CrawlRepository
from domain.game import Game
from infra.db.base.db import session_scope


class CrawlBGGGameUseCaseImpl(CrawlBGGGameUseCase):
    def __init__(
        self,
        parser: BGGGameParserService,
        games_repo: GamesRepository,
        target_repo: TargetGamesRepository,
        crawl_repo: CrawlRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self.parser = parser
        self.games_repo = games_repo
        self.target_repo = target_repo
        self.crawl_repo = crawl_repo
        self.logger = logger or logging.getLogger(__name__)

    def execute(self, pages: int) -> Dict[str, Any]:
        """
        指定ページ数分のランキング（各100件）と target_games の bgg_id を収集し、
        既存IDと候補IDをマージして重複排除した全IDを対象にパースして保存する。
        終了後、crawl_progress に結果を記録する。
        """
        if pages < 0:
            raise ValueError("pages は 0 以上で指定してください")

        # バッチメタ情報
        started_at = datetime.datetime.utcnow()
        batch_type = "ranking" if pages > 0 else "manual"
        batch_id = f"crawl-{batch_type}-{started_at.strftime('%Y%m%d-%H%M%S')}"

        # 1) 対象 bgg_id 候補を収集
        candidate_ids: Set[int] = set(self.target_repo.list_all_bgg_id())
        if pages > 0:
            for p in range(1, pages + 1):
                try:
                    ids = self.parser.parse_ranking_ids(p)
                    candidate_ids.update(ids)
                except Exception as e:
                    self.logger.warning(f"ランキングページ {p} の取得でエラー: {e}")

        # 2) 既存 games の bgg_id を取得し、候補とマージ（distinct）
        existing_ids: Set[int] = set(self.games_repo.list_all_bgg_id())
        merged_ids_sorted: List[int] = sorted(candidate_ids.union(existing_ids))

        # このユースケースでは差分ではなくマージ結果を全て取得対象にする
        to_fetch_ids: List[int] = merged_ids_sorted

        # 3) パース＆蓄積（簡易実装）
        parsed_games: List[Game] = []
        failed_ids: List[int] = []

        for bgg_id in to_fetch_ids:
            try:
                game = self.parser.parse_game(bgg_id)
                if game:
                    parsed_games.append(game)
                else:
                    failed_ids.append(bgg_id)
            except Exception as e:
                self.logger.warning(f"bgg_id={bgg_id} のパース失敗: {e}")
                failed_ids.append(bgg_id)

        # 4) bulk upsert
        bgg_to_game_id: Dict[int, int] = {}
        if parsed_games:
            bgg_to_game_id = self.games_repo.bulk_create_games(parsed_games)

        stored_count = len(bgg_to_game_id)
        failed_count = len(failed_ids)
        total_candidates = len(merged_ids_sorted)
        completed_at = datetime.datetime.utcnow()

        # 5) crawl_progress へ結果登録
        with session_scope() as session:
            progress = self.crawl_repo.create(
                session=session,
                batch_id=batch_id,
                total_games=total_candidates,
                batch_type=batch_type,
                started_at=started_at,
            )
            progress.processed_games = stored_count
            progress.failed_games = failed_count
            progress.completed_at = completed_at
            if failed_ids:
                preview = ", ".join(str(x) for x in failed_ids[:10])
                progress.error_message = f"failed_ids(first10): {preview}"

        # 6) サマリー
        return {
            "batch_id": batch_id,
            "batch_type": batch_type,
            "requested_pages": pages,
            "candidates": total_candidates,
            "existing": len(existing_ids),
            "to_fetch": len(to_fetch_ids),
            "stored": stored_count,
            "failed": failed_count,
            "failed_ids": failed_ids[:50],
            "started_at": started_at.isoformat() + "Z",
            "completed_at": completed_at.isoformat() + "Z",
        }