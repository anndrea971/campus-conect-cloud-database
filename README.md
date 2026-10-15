# Overview

As a software engineer, I wanted to learn how to build applications that store and share data through a managed cloud database instead of a local file or a self-hosted server. To do that, I moved my CampusConnect project into a cloud-backed study agenda system written in Python. It uses Google Cloud Firestore through the `firebase-admin` library.

The program lets students create study groups, schedule study sessions for those groups, and keep meeting details (agenda, date, and meeting link) in one shared place. Everything is stored in Firestore, so the data persists between runs and can be reached from any machine that has the service account credentials.

How to use the program:

1. Install the dependency: `pip install firebase-admin`
2. Create a Firebase project and a Firestore database, then download a Service Account JSON key. Save it in the project folder (it is listed in `.gitignore` and is never committed).
3. Update the key file name and project settings at the top of the program if needed.
4. Run the program with `python main.py` and pick an option from the menu:
   - **Insert**: create a new study group or schedule a new meeting for a group.
   - **Retrieve**: list all study groups, or list the meetings for a specific course or group.
   - **Modify**: change a meeting's link, date, or agenda, or update a group's course topic.
   - **Delete**: remove a canceled meeting or an inactive study group.

My purpose for writing this software was to practice the full set of cloud database operations (insert, retrieve, modify, delete) and to learn how to model related data in a NoSQL database, where there are no joins and relationships have to be designed deliberately.

{Replace the link below with your YouTube demo: 4-5 minutes showing the software running, a code walkthrough, and the Firestore console.}

[Software Demo Video](http://youtube.link.goes.here)

# Cloud Database

I am using **Google Cloud Firestore**, a serverless NoSQL document database that is part of Google Firebase. Data is stored as documents (key/value maps) inside collections, and it can be queried in whole, in parts, or filtered by field values. The Python program connects with the Firebase Admin SDK using a Service Account key.

The database has two related collections:

**StudyGroups**

| Field | Description |
|---|---|
| `course_title` | Course the group studies for (e.g. "CSE 310") |
| `topic` | Group topic or focus |
| `owner` | Student who created the group |

**Meetings**

| Field | Description |
|---|---|
| `group_id` | Document ID of the related StudyGroup (the relationship) |
| `course_title` | Course the session is for, stored to allow queries by course |
| `date` | Date and time of the session |
| `agenda` | What will be covered in the session |
| `meeting_link` | URL for the session |

Each meeting stores the ID of its study group in `group_id`, so all meetings for a group can be found with a simple query (`where("group_id", "==", ...)`). When a study group is deleted, its meetings are removed as well so that no orphaned meeting documents remain.

# Development Environment

- VSC and Github
- Firebase Console to create the project, manage the Firestore database, and inspect the stored data while testing
- Python 3 as the programming language
- Libraries: `firebase-admin` (Firestore access and authentication with the Service Account key) and the Python standard library (`datetime`, etc.)

# Useful Websites

- [Cloud Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Firebase Admin SDK Setup](https://firebase.google.com/docs/admin/setup)
- [Firestore: Add Data](https://firebase.google.com/docs/firestore/manage-data/add-data)
- [Firestore: Get Data and Run Queries](https://firebase.google.com/docs/firestore/query-data/queries)
- [Firestore: Choose a Data Structure](https://firebase.google.com/docs/firestore/manage-data/structure-data)

# Future Work

- Add user authentication so students can only edit or delete the groups they own
- Add real-time notifications when a meeting's link or time changes
- Add input validation for dates and meeting links
- Add a group membership list so students can join and leave study groups
- Build a simple graphical or web interface on top of the existing functions
