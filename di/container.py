# python
# di/container.py
from __future__ import annotations

import os
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

from adapter.service.bgg_game_parser_service_impl import BGGGameParserServiceImpl
from infra.db.crawl_repository_impl import CrawlRepositoryImpl
from infra.db.games_repository_impl import GamesRepositoryImpl
from infra.db.target_games_repository_impl import TargetGamesRepositoryImpl
from infra.http.selenium_http_client import SeleniumHttpClient
from usecase.crawl_bgg_game_usecase_impl import CrawlBGGGameUseCaseImpl


@dataclass
class AppConfig:
    # Selenium/HTTP
    headless: bool = True
    http_timeout: int = 25
    user_agent: str = "BGGGameCrawler/1.0 (+contact: <contact@example.com>)"
    save_html: bool = False
    output_dir: str = "output"

    # Politeness
    min_delay_seconds: float = 5.0   # robots.txt Crawl-delay
    jitter_min: float = 0.0
    jitter_max: float = 3.0
    max_retries: int = 2
    backoff_base_seconds: float = 10.0
    backoff_cap_seconds: float = 120.0

    # Logging
    log_level: int = logging.INFO

    @classmethod
    def from_env(cls) -> "AppConfig":
        def _bool(name: str, default: bool) -> bool:
            v = os.getenv(name)
            if v is None:
                return default
            return v.lower() in ("1", "true", "yes", "on")
        def _int(name: str, default: int) -> int:
            v = os.getenv(name)
            return int(v) if v is not None and v.isdigit() else default
        def _float(name: str, default: float) -> float:
            v = os.getenv(name)
            try:
                return float(v) if v is not None else default
            except ValueError:
                return default

        return cls(
            headless=_bool("BGG_HEADLESS", True),
            http_timeout=_int("BGG_HTTP_TIMEOUT", 25),
            user_agent=os.getenv("BGG_USER_AGENT", "BGGGameCrawler/1.0 (+contact: <contact@example.com>)"),
            save_html=_bool("BGG_SAVE_HTML", False),
            output_dir=os.getenv("BGG_OUTPUT_DIR", "output"),
            min_delay_seconds=_float("BGG_MIN_DELAY_SECONDS", 5.0),
            jitter_min=_float("BGG_JITTER_MIN", 0.0),
            jitter_max=_float("BGG_JITTER_MAX", 3.0),
            max_retries=_int("BGG_MAX_RETRIES", 2),
            backoff_base_seconds=_float("BGG_BACKOFF_BASE_SECONDS", 10.0),
            backoff_cap_seconds=_float("BGG_BACKOFF_CAP_SECONDS", 120.0),
            log_level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
        )

    @property
    def jitter_range(self) -> Tuple[float, float]:
        return (self.jitter_min, self.jitter_max)


@contextmanager
def provide_crawl_usecase(config: Optional[AppConfig] = None) -> Iterator[CrawlBGGGameUseCaseImpl]:
    """
    Selenium のライフサイクルを含めて依存をまとめて作成し、ユースケースを提供する。
    """
    cfg = config or AppConfig.from_env()

    logging.basicConfig(level=cfg.log_level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    with SeleniumHttpClient(
        headless=cfg.headless,
        timeout=cfg.http_timeout,
        user_agent=cfg.user_agent,
        save_html=cfg.save_html,
        output_dir=cfg.output_dir,
        min_delay_seconds=cfg.min_delay_seconds,
        jitter_range=cfg.jitter_range,
        max_retries=cfg.max_retries,
        backoff_base_seconds=cfg.backoff_base_seconds,
        backoff_cap_seconds=cfg.backoff_cap_seconds,
        block_images=True,
        block_fonts=True,
        block_media=True,
    ) as http_client:
        parser = BGGGameParserServiceImpl(http_client=http_client, timeout=cfg.http_timeout, user_agent=cfg.user_agent)
        games_repo = GamesRepositoryImpl()
        target_repo = TargetGamesRepositoryImpl()
        crawl_repo = CrawlRepositoryImpl()

        usecase = CrawlBGGGameUseCaseImpl(
            parser=parser,
            games_repo=games_repo,
            target_repo=target_repo,
            crawl_repo=crawl_repo,
            logger=logging.getLogger("CrawlBGGGameUseCase"),
        )
        yield usecase


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")