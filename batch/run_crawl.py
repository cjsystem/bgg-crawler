# python
# scripts/run_crawl.py
import json
from di.container import AppConfig, provide_crawl_usecase

def main():
    cfg = AppConfig.from_env()
    with provide_crawl_usecase(cfg) as usecase:
        result = usecase.execute(pages=10)
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()