#!/usr/bin/env python3
"""Stage and validate a fresh edition before replacing dashboard data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent

# Transparent, reproducible title/long-title matching; editorial tagging is not
# supplied by Parliament. Existing hand-curated tags are retained by bill ID.
RULES = {
    'Health and social care': r'health|\bhospitals?\b|medical|cancer|care service|\bnhs\b',
    'Constitution, elections and rights': r'constitution|election|parliament|house of lords|human rights|representation of the people',
    'Business, work and employment': r'employment|worker|business|commercial|trade union',
    'Housing and planning': r'housing|homes|planning|leasehold|building safety|cladding|renters',
    'Economy and taxation': r'finance|tax|levy|treasury|sovereign grant',
    'Transport and roads': r'transport|railway|highway|road|aviation|parking|vehicle',
    'Family, children and equality': r'children|child|family|equality|parental',
    'Energy and utilities': r'energy|electricity|gas supply|water supply|utilities',
    'Education and skills': r'education|school|skills|university',
    'Justice and courts': r'court|tribunal|justice|sentencing|prison',
    'Environment and climate': r'environment|climate|pollution|recycling|biodiversity',
    'International and trade': r'international|trade agreement|export|import',
    'Policing and public safety': r'police|policing|crime|terrorism|public safety',
    'Local government and communities': r'local government|local authorit|community|communities',
    'Social welfare and benefits': r'social security|benefit|pension|welfare payment',
    'Digital, data and AI': r'digital|data|artificial intelligence|software|cyber|online',
    'Immigration and citizenship': r'immigration|asylum|citizenship|nationality',
    'Culture, sport and media': r'culture|sport|media|broadcast|football',
    'Defence and armed forces': r'defence|armed forces|military|submarine',
    'Agriculture, food and fisheries': r'agriculture|food|fisher|farm',
    'Science and research': r'science|research|space',
    'Animals and animal welfare': r'\banimal\w*|\breindeer\b|\bdogs?\b|\bcats?\b|\bferrets?\b',
    'Fire and emergency services': r'fire service|fire and rescue|emergency service',
}

def load(path):
    return json.loads(path.read_text())

def run(*args):
    subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, check=True)

def main():
    import re
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, help='Use an already freshly downloaded JSON file')
    ap.add_argument('--csv', type=Path, help='Matching raw CSV for --input')
    args = ap.parse_args()
    if bool(args.input) != bool(args.csv):
        ap.error('--input and --csv must be supplied together')
    original = load(ROOT / 'data/bills.json')
    stamp = original['downloaded_at'][:10]
    archive = ROOT / 'archives' / ('snapshot-' + original['downloaded_at'].replace(':', '-'))
    # Never overwrite an earlier archive. The original edition has a named archive.
    existing = ROOT / 'archives/starmer-2026-01-02'
    if not (stamp == '2026-01-02' and existing.exists()) and not archive.exists():
        shutil.copytree(ROOT / 'data', archive / 'data')
        hashes = {str(p.relative_to(archive)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in archive.rglob('*') if p.is_file()}
        (archive / 'manifest.json').write_text(json.dumps({'files': hashes}, indent=2))
    with tempfile.TemporaryDirectory(prefix='bills-refresh-') as tmp:
        stage = Path(tmp)
        if args.input:
            shutil.copy2(args.input, stage / 'bills.json')
            shutil.copy2(args.csv, stage / 'bills.csv')
        else:
            run(ROOT / 'src/download.py', '--json', stage / 'bills.json', '--csv', stage / 'bills.csv', '--workers', '12', '--debug')
        raw = load(stage / 'bills.json')
        items = raw.get('items', [])
        if not items or len({b['bill_id'] for b in items}) != len(items) or any(b.get('detail_ok') != 1 for b in items):
            raise RuntimeError('Incomplete or duplicate bill download; dashboard data left unchanged')
        run(ROOT / 'src/simplify.py', '--in', stage / 'bills.json', '--json', stage / 'bills_simplified.json', '--csv', stage / 'bills_simplified.csv')
        run(ROOT / 'src/statistics.py', '--in', stage / 'bills.json', '--out', stage / 'statistics.json')
        run(ROOT / 'src/members.py', '--in', stage / 'bills.json', '--out', stage / 'members.json')
        bills = load(stage / 'bills_simplified.json')['items']
        old_topics = load(ROOT / 'data/topics.json')['data']
        old_ids = {b['bill_id'] for b in load(ROOT / 'data/bills_simplified.json')['items']}
        valid_ids = {b['bill_id'] for b in bills}
        topics = {t['name']: dict(t, bills=[i for i in t['bills'] if i in valid_ids]) for t in old_topics}
        for b in bills:
            if b['bill_id'] in old_ids:
                continue
            text = b['short_title'] + ' ' + b['long_title']
            matches = [name for name, pattern in RULES.items() if re.search(pattern, text, re.I)] or ['Other']
            for name in matches:
                topics[name]['bills'].append(b['bill_id'])
        for t in topics.values():
            t['bills'] = sorted(set(t['bills']), reverse=True)
            t['count'] = len(t['bills'])
        (stage / 'topics.json').write_text(json.dumps({'method': 'Original editorial tags retained; new bill IDs use keyword matching against title and long title. Multiple topics allowed.', 'data': list(topics.values())}, indent=2))
        latest = max(b.get('last_update') or '' for b in items)
        captured = raw['downloaded_at'][:10]
        edition = {'label': '2026 — Burnham era', 'downloaded_at': raw['downloaded_at'],
                   'latest_bill_update': latest, 'target_year_end': '2026-12-31',
                   'prime_minister': 'Andy Burnham', 'premiership_start': '2026-07-20',
                   'context_source': 'https://www.gov.uk/government/people/andy-burnham',
                   'scope': 'Full historical API corpus; includes Acts, backbench bills and earlier governments',
                   'coverage_note': f'Snapshot downloaded {captured}; latest bill update {latest[:10]}. Working edition for year-end 2026; refresh after 31 December for final year-end figures.'}
        (stage / 'edition.json').write_text(json.dumps(edition, indent=2) + '\n')
        for name in ['bills_simplified.json', 'statistics.json']:
            obj = load(stage / name)
            obj['source'] = 'data/bills.json'
            (stage / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
        # All derivation/validation has succeeded before touching current files.
        for p in stage.iterdir():
            shutil.copy2(p, ROOT / 'data' / p.name)
        print(f'Refreshed {len(items)} bill records; {len(bills)} distinct titles. Latest update: {latest}')

if __name__ == '__main__':
    main()
