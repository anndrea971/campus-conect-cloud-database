"""
CampusConnect - Cloud Study Agenda
Module #3: Cloud Databases (Python + Google Cloud Firestore)

Students can create study groups and schedule study sessions (meetings)
for those groups. Data lives in two related Firestore collections:

  StudyGroups: course_title, topic, owner
  Meetings:    group_id (-> StudyGroups document ID), course_title,
               date, agenda, meeting_link
"""

from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Name of the secret Service Account file (never committed to GitHub)
SERVICE_ACCOUNT_FILE = "serviceAccountKey.json"

# Collection names
GROUPS = "StudyGroups"
MEETINGS = "Meetings"

# Format used when typing and storing meeting dates
DATE_FORMAT = "%Y-%m-%d %H:%M"


def connect_to_database():
    """Initialize the Firebase Admin SDK and return a Firestore client."""
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred)
    return firestore.client()


def ask_date(prompt):
    """Keep asking until the user types a valid date/time, then return it as text."""
    while True:
        value = input(prompt + " (YYYY-MM-DD HH:MM): ").strip()
        try:
            # Parsing proves the format is valid; we store the clean string
            datetime.strptime(value, DATE_FORMAT)
            return value
        except ValueError:
            print("  Invalid date. Example: 2026-10-20 18:30")


def group_exists(db, group_id):
    """Return True if a StudyGroup document with this ID exists."""
    return db.collection(GROUPS).document(group_id).get().exists


# ---------------------------------------------------------------- INSERT

def add_study_group(db):
    """Insert a new study group document and print its generated ID."""
    data = {
        "course_title": input("Course title (e.g. CSE 310): ").strip(),
        "topic": input("Group topic: ").strip(),
        "owner": input("Owner name: ").strip(),
    }
    # add() returns (timestamp, document_reference); we only need the reference
    _, ref = db.collection(GROUPS).add(data)
    print(f"Study group created. ID: {ref.id}")


def add_meeting(db):
    """Insert a new meeting linked to an existing study group."""
    group_id = input("Study group ID: ").strip()
    group_doc = db.collection(GROUPS).document(group_id).get()

    # Relational check: a meeting must always point to a real group
    if not group_doc.exists:
        print("No study group found with that ID.")
        return

    data = {
        "group_id": group_id,
        # Copy the course so meetings can be queried by course directly
        "course_title": group_doc.to_dict()["course_title"],
        "date": ask_date("Meeting date and time"),
        "agenda": input("Agenda: ").strip(),
        "meeting_link": input("Meeting link: ").strip(),
    }
    _, ref = db.collection(MEETINGS).add(data)
    print(f"Meeting scheduled. ID: {ref.id}")


# -------------------------------------------------------------- RETRIEVE

def list_study_groups(db):
    """Retrieve and print every study group."""
    docs = list(db.collection(GROUPS).stream())
    if not docs:
        print("No study groups yet.")
        return
    for doc in docs:
        g = doc.to_dict()
        print(f"[{doc.id}] {g['course_title']} - {g['topic']} (owner: {g['owner']})")


def print_meetings(docs):
    """Print a list of meeting documents sorted by date."""
    meetings = sorted(docs, key=lambda d: d.to_dict()["date"])
    if not meetings:
        print("No meetings found.")
        return
    for doc in meetings:
        m = doc.to_dict()
        print(f"[{doc.id}] {m['date']} | {m['course_title']} | {m['agenda']}")
        print(f"      link: {m['meeting_link']}  (group: {m['group_id']})")


def list_meetings_by_course(db):
    """Query Firestore for all meetings of one course."""
    course = input("Course title: ").strip()
    query = db.collection(MEETINGS).where(
        filter=FieldFilter("course_title", "==", course)
    )
    print_meetings(list(query.stream()))


def list_meetings_by_group(db):
    """Query Firestore for all meetings that belong to one study group."""
    group_id = input("Study group ID: ").strip()
    query = db.collection(MEETINGS).where(
        filter=FieldFilter("group_id", "==", group_id)
    )
    print_meetings(list(query.stream()))


# ---------------------------------------------------------------- MODIFY

def update_meeting(db):
    """Update the link, date, or agenda of an existing meeting."""
    meeting_id = input("Meeting ID: ").strip()
    ref = db.collection(MEETINGS).document(meeting_id)
    if not ref.get().exists:
        print("No meeting found with that ID.")
        return

    print("What do you want to change?  1) Link  2) Date/time  3) Agenda")
    choice = input("Choice: ").strip()
    if choice == "1":
        updates = {"meeting_link": input("New meeting link: ").strip()}
    elif choice == "2":
        updates = {"date": ask_date("New date and time")}
    elif choice == "3":
        updates = {"agenda": input("New agenda: ").strip()}
    else:
        print("Invalid choice.")
        return

    # update() changes only the given fields and leaves the rest untouched
    ref.update(updates)
    print("Meeting updated.")


def update_group_topic(db):
    """Update the topic of a study group."""
    group_id = input("Study group ID: ").strip()
    ref = db.collection(GROUPS).document(group_id)
    if not ref.get().exists:
        print("No study group found with that ID.")
        return
    ref.update({"topic": input("New topic: ").strip()})
    print("Study group updated.")


# ---------------------------------------------------------------- DELETE

def delete_meeting(db):
    """Delete a single canceled meeting."""
    meeting_id = input("Meeting ID: ").strip()
    ref = db.collection(MEETINGS).document(meeting_id)
    if not ref.get().exists:
        print("No meeting found with that ID.")
        return
    ref.delete()
    print("Meeting deleted.")


def delete_study_group(db):
    """Delete a study group AND all of its meetings (avoids orphan data)."""
    group_id = input("Study group ID: ").strip()
    if not group_exists(db, group_id):
        print("No study group found with that ID.")
        return

    # Find every meeting that points to this group
    meetings = db.collection(MEETINGS).where(
        filter=FieldFilter("group_id", "==", group_id)
    ).stream()

    # A batch makes all deletes succeed or fail together
    batch = db.batch()
    count = 0
    for doc in meetings:
        batch.delete(doc.reference)
        count += 1
    batch.delete(db.collection(GROUPS).document(group_id))
    batch.commit()
    print(f"Study group deleted along with {count} meeting(s).")


# ------------------------------------------------------------------ MENU

MENU = """
=== CampusConnect Study Agenda ===
 1) Create study group
 2) Schedule meeting
 3) List study groups
 4) List meetings by course
 5) List meetings by group
 6) Update meeting (link/date/agenda)
 7) Update study group topic
 8) Delete meeting
 9) Delete study group (and its meetings)
 0) Exit
"""


def main():
    """Connect to Firestore and run the menu loop until the user exits."""
    db = connect_to_database()

    # Map each menu choice to the function that handles it
    actions = {
        "1": add_study_group,
        "2": add_meeting,
        "3": list_study_groups,
        "4": list_meetings_by_course,
        "5": list_meetings_by_group,
        "6": update_meeting,
        "7": update_group_topic,
        "8": delete_meeting,
        "9": delete_study_group,
    }

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action(db)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
