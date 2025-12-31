import sys
import os
import json
from app.utils.database import SessionLocal
from app.models.editor.database import EditorProjectDB

def test_editor_projects():
    db = SessionLocal()
    try:
        projects = db.query(EditorProjectDB).all()
        print(f"--- Database Check: Found {len(projects)} projects in 'editor_projects' table ---")
        for p in projects:
            print(f"ID: {p.id}")
            print(f"Name: {p.name}")
            print(f"Status: {p.status}")
            print(f"Output: {p.output_path}")
            if p.timeline_json:
                print("Timeline: Has data")
            else:
                print("Timeline: EMPTY")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_editor_projects()
