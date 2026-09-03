import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .catalog import CATALOG_PATH, _active


def refresh_snapshot(path=CATALOG_PATH, today=None):
    path = Path(path)
    payload = json.loads(path.read_text(encoding='utf-8'))
    check_date = today or date.today()
    items = [item for item in payload.get('items', []) if isinstance(item, dict) and _active(item, check_date)]
    items.sort(key=lambda item: (item.get('deadline') or '9999-12-31', item.get('title') or ''))
    refreshed = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'count': len(items),
        'items': items,
    }
    path.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return refreshed


def main():
    parser = argparse.ArgumentParser(description='Remove closed scholarships and refresh the public scholarship snapshot.')
    parser.add_argument('--output', default=str(CATALOG_PATH))
    args = parser.parse_args()
    payload = refresh_snapshot(args.output)
    print(f"Published {payload['count']} active scholarships to {args.output}")


if __name__ == '__main__':
    main()
