"""Read-only A05 plan validation. Never launches scientific units."""
import argparse,csv,json,hashlib
from pathlib import Path
from plan_contract import validate_plan,next_gate
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--coverage',type=Path,required=True);p.add_argument('--expected-plan-sha256',required=True);a=p.parse_args()
 assert hashlib.file_digest(a.plan.open('rb'),'sha256').hexdigest()==a.expected_plan_sha256
 plan=json.loads(a.plan.read_text());assert hashlib.file_digest(a.coverage.open('rb'),'sha256').hexdigest()==plan['coverage_csv_sha256'];rows=list(csv.DictReader(a.coverage.open()));result=validate_plan(plan,rows);result.update(next_proposed_gate=next_gate('R4',set()),execution='NOT_STARTED; direct A06 approval required');print(json.dumps(result))
if __name__=='__main__':main()
