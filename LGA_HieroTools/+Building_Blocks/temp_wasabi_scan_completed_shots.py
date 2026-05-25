import os
import sqlite3
import sys
from collections import defaultdict


def get_db_path():
    return r"C:/Portable/LGA/PipeSync/cache/pipesync.db"


def get_completed_shots_from_db(db_path):
    status_map = {
        "apr": "approved",
        "approved": "approved",
        "check": "delivery_checked",
        "delivery_checked": "delivery_checked",
    }
    statuses = tuple(status_map.keys())

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        placeholders = ",".join(["?"] * len(statuses))
        query = f"""
            SELECT shot_name, shot_status
            FROM shots
            WHERE shot_status IN ({placeholders})
            ORDER BY shot_name
        """
        rows = cur.execute(query, statuses).fetchall()
        return {shot_name: status_map.get(status, status) for shot_name, status in rows}
    finally:
        conn.close()


def get_iam_client():
    startup_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    flow_dir = os.path.join(startup_dir, "LGA_NKS_Flow")
    wasabi_dir = os.path.join(startup_dir, "LGA_NKS_Wasabi")
    sys.path.insert(0, flow_dir)
    sys.path.insert(0, wasabi_dir)

    from SecureConfig_Reader import get_s3_credentials
    from boto3 import Session

    access_key, secret_key, endpoint, region = get_s3_credentials()
    if not access_key or not secret_key:
        raise RuntimeError("No se pudieron obtener credenciales de Wasabi")

    session = Session()
    return session.client(
        "iam",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url="https://iam.wasabisys.com",
        region_name=region or "us-east-1",
    )


def iter_local_policies(iam_client):
    marker = None
    while True:
        kwargs = {"Scope": "Local"}
        if marker:
            kwargs["Marker"] = marker
        data = iam_client.list_policies(**kwargs)
        for policy in data.get("Policies", []):
            yield policy
        if not data.get("IsTruncated"):
            break
        marker = data.get("Marker")


def get_default_policy_document(iam_client, policy_arn):
    policy = iam_client.get_policy(PolicyArn=policy_arn)["Policy"]
    version_id = policy["DefaultVersionId"]
    return iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)[
        "PolicyVersion"
    ]["Document"]


def extract_shots_from_policy(policy_doc):
    shots = set()
    for statement in policy_doc.get("Statement", []):
        if statement.get("Action") != "s3:*":
            continue
        resources = statement.get("Resource", [])
        if isinstance(resources, str):
            resources = [resources]
        for resource in resources:
            if not isinstance(resource, str):
                continue
            if not resource.startswith("arn:aws:s3:::"):
                continue
            if "/" not in resource:
                continue
            shot_name = resource.rstrip("/").split("/")[-1]
            if shot_name and shot_name != "*":
                shots.add(shot_name)
    return shots


def main():
    db_path = get_db_path()
    completed_shots = get_completed_shots_from_db(db_path)
    print(f"DB: {db_path}")
    print(f"Shots completados detectados: {len(completed_shots)}")

    iam = get_iam_client()
    matches = []
    per_policy_count = defaultdict(int)

    for policy in iter_local_policies(iam):
        policy_name = policy.get("PolicyName", "")
        if not policy_name.endswith("_policy"):
            continue
        policy_arn = policy["Arn"]
        try:
            policy_doc = get_default_policy_document(iam, policy_arn)
        except Exception as exc:
            print(f"[WARN] No se pudo leer policy {policy_name}: {exc}")
            continue

        policy_shots = extract_shots_from_policy(policy_doc)
        for shot_name in policy_shots:
            if shot_name in completed_shots:
                matches.append((policy_name, shot_name, completed_shots[shot_name]))
                per_policy_count[policy_name] += 1

    matches.sort(key=lambda row: (row[0], row[1]))
    print(f"Coincidencias policy-shot completados: {len(matches)}")
    for policy_name, shot_name, shot_status in matches:
        print(f"{policy_name} | {shot_name} | {shot_status}")

    target = "PHLDA_068_020_Chroma_LivingNoche"
    target_matches = [m for m in matches if m[1] == target]
    if target_matches:
        print("\nSHOT OBJETIVO ENCONTRADO:")
        for row in target_matches:
            print(f"{row[0]} | {row[1]} | {row[2]}")
    else:
        print("\nSHOT OBJETIVO NO ENCONTRADO EN POLICIES:", target)


if __name__ == "__main__":
    main()
