# IST Tutoring Portal

This portal is a web based interface to handle student help requests in the University of Nebraska at Omaha Computer Science Learning Center.

## Table of Contents

* Table of Contents
* Use
    * Home Page
    * Students
        * Open Ticket
        * Status
    * Tutor Login
    * Logout
    * Tutors
        * Edit User
        * View Tickets
            * Claim/Close Ticket
            * Reopen Ticket
    * Administrators
        * Administration Console
            * Messages
            * Courses
            * Course Sections
            * Semesters
            * Professors
            * Problem Types
            * Tutors
        * Reports
            * Download Report
            * Ticket Details
* Appendix A. Setup and Installation

## Use

### Home Page

Logged in:
![Homepage](screenshots/homepage.png)

Logged out with message:
![Homepage with Message](screenshots/homepage-message.png)

The home page is the first page displayed to the user. In the final version of the system it will be located at <https://tutoring.ist.unomaha.edu/>. The home page includes links to the `Open Ticket` and `View Tickets` pages in the body. The toolbar also contains a link to the `Status` page and either `Tutor Login` or `Logout` based on whether the user is logged in. Additionally, the Computer Science Learning Center logo above the toolbar is a link to the homepage.

If a tutor is logged in an extra `Tutor` dropdown will be in the toolbar with links for the `Edit User` and `View Tickets` pages. If an administrator is logged in, an `Admin` dropdown will be available in addition to the `Tutor` dropdown. The `Admin` console contains an `Admin Console` link to the administration console, and a `Reports` link to the reports page.

The toolbar and logo are displayed on all pages, but have been omitted from screenshots to save space.

### Students

Students do not need to log in to the system. While not logged in, two features are accessible, opening tickets and the status page.

#### Open Ticket

![Open Ticket Page](screenshots/open-ticket.png)

A ticket can be opened by clicking the `Open Ticket` button on the home page. This opens the Open Ticket form.

On the form, a student must enter their Email, First Name, Last Name, Course and Section, Assignment Name, Specific Question, and Problem Type.

The Email, First Name, and Last Name are the personal contact information for the student requesting the session. If a group is requesting tutoring only the contact information for the group leader should be entered.

The Course selection filters the Section options based on the course selected.

The Section selection is the course section the student is requesting tutoring for.

The Assignment Name is the name of the assignment the student is requesting help with. This is usually similar to "Assignment 1" or "Project 1".

The Specific Question is the question the student is asking or a topic they need to know more about. Students should be instructed to be as specific as possible.

The Problem Type is a selection of the categories of problems that students may encounter. This helps determine the stage of problem solving they are at.

Once all of the fields are filled out, the ticket is submitted with the `Submit` button. The page is protected by a CAPTCHA so students may be asked to respond to the CAPTCHA before the ticket is submitted.

#### Status

![Status Page](screenshots/status.png)

The status screen gives an overview of the situation in the tutoring center. It can be accessed by clicking the `Status` button in the toolbar. The status screen has three sections.

The `Messages` section displays any current messages entered by an administrator.

The `Course Availability` section gives the current number of tickets and tutors in the tutoring center for courses selected by an administrator. This shows how busy the tutoring center is and whether there are tutors available to students planning on getting help.

The last section, `Open Tickets` only displays for logged in users. It shows the current list of open tickets.

### Tutor Login

To perform any tutor or administrator actions the tutor or administrator must be logged in. To log in, click the `Tutor Login` button in the toolbar. This will redirect to a Google login page. Log in using the email for your account (usually an `@unomaha.edu` account). If this is the account's first time logging in access must be granted for the application to view the account's email address. The tutor will then be logged in if the account they used to log in is a valid, active tutor account or rejected otherwise. Either way, they will be redirected back to the application's home page and a message will be displayed indicating whether login was successful.

### Logout

To logout, a tutor can click the `Logout` button in the toolbar. They will be logged out and redirected to the home page with a logout confirmation.

### Tutors

#### Edit User

![Edit User Page](screenshots/edit-user.png)

Tutors can edit a subset of the information about themself by clicking `Tutor` in the toolbar, then `Edit User`. Administrators will be redirected to the Edit Tutor page for themself, while normal tutors will be shown a subset of the fields accessible to administrators.

Tutors can edit their First Name, Last Name, Currently Working status, and Can Tutor course proficiencies. For detailed instructions see the Tutors page description below.

#### View Tickets

![View Tickets Page](screenshots/view-tickets.png)

Tutors can. The tickets list can be accessed by clicking `Tutor` in the toolbar, then `View Tickets` or by clicking `View Tickets` on the homepage.

The view tickets page has three sections. `Open` is for tickets not yet claimed by a tutor. `Claimed` is for tickets that have been claimed, but the session is not yet finished. `Closed` is for tickets for which the session has been finished.

##### Claim/Close Ticket

![Claim/Close Ticket Page](screenshots/close-ticket.png)

Tickets in the `Open` section have a `Claim` button and tickets in the `Claimed` section have a `Close` button. Both of these lead to the Claim/Close page for the selected ticket.

On the Claim/Close page tutors can edit the ticket course and section, assignment name, question, problem type, claiming tutor, assisting tutor, and whether the session was successful. The Claiming Tutor is the tutor that helped the student during the session. The Assisting Tutor is for if another tutor provided input during the session. Session Duration indicates the actual amount of time that the tutor spent with a student. Was Successful indicates if the original question for the session was resolved. The purposes of the rest of the fields are described in the Open Ticket page description above. All of these fields are required except the assisting tutor.

Once the necessary fields are filled out the ticket can be assigned to the `Claimed` section by clicking the `Claim` button or the `Closed` section by clicking the `Close` button.

##### Reopen Ticket

Tickets in the `Closed` section have a `Reopen` button. Clicking this moves the ticket from the `Closed` section back to the `Claimed` section, altering its status accordingly. The rest of the tickets details remain the same.

### Administrators

#### Administration Console

![Admin Console Page](screenshots/admin-console.png)

The administration console is where the administrator can set up tutor accounts, messages, problem types, and all of the information necessary for course sections.

The Administration Console can be accessed when logged in as an administrator by clicking `Admin` in the toolbar, followed by `Admin Console`. If the `Admin` option does not exist you are not logged in as an administrator.

On the Administration Console page there are links to menus for Messages, Courses, Course Sections, Semesters, Professors, Problem Types, and Tutors. By clicking each link, menus can be accessed that allow editing and viewing of objects of each type.

**Before adding a Course Section, the corresponding Course, Semester, and Professor must be added. Before students can open tickets, there must be a Course Section for the current Semester and at least one Problem Type.**

![Admin List Page](screenshots/list.png)

Each menus is the same, with a `+ New` button to create a new object and `Edit` buttons to change the details of an existing object. The screen for editing is the same as for creating an object, but the existing details are already filled in. The object is saved or created by clicking the submit button.

##### Messages

![Edit Message Page](screenshots/message.png)

Messages display on the status screen. A message will not display before its Start Date or after its End Date. The message's Message is converted to HTML using [Markdown](...) syntax.

Messages are sorted by their end date.

##### Courses

![Edit Course Page](screenshots/course.png)

Courses allow students to select sections and group tickets on the status page. The Course Number is the department and number listed in the course catalog (eg. CIST 1400). The Course Name is the name of the course in the catalog (eg. Introduction to Computer Programming). The Display on Status Page field will select the course to have its number of tickets and tutors shown on the status page if checked.

Courses are always sorted by their number.

##### Course Sections

![Edit Section Page](screenshots/section.png)

Course Sections are the individual classes taught for each course. The Semester is the university semester that the course is taught during. A section will only be available for students to open tickets for during the selected semester. The Course is the course that a section belongs to. The Number is the section number in the course catalog. The Time is a description of when the class is held. The Professor is who is teaching the class.

Course Sections are sorted by their semester, and by their course number within each semester, and by their own number within each course.

##### Semesters

![Edit Semester Page](screenshots/semester.png)

Semesters group course sections to a university semester. The Year is the year a semester is held during. The Season is the part of the year a semester is held during. The Start Date is the first day of the semester and the End Date is the last day of the semester. Course sections for a semester will not be available for opening tickets outside of these dates.

Semesters are sorted by their start date.

##### Professors

![Edit Professor Page](screenshots/professor.png)

Professors are the teachers for course sections. The First Name and Last Name set the first and last name for the professor.

Professors are sorted by their last name.

##### Problem Types

![Edit Problem Page](screenshots/problem.png)

Problem Types are the categories of issues students may be experiencing. The description is a short summary of the type of problem.

Problem Types are sorted by their description.

##### Tutors

![Edit Tutor Page](screenshots/tutor.png)

![New Tutor Page](screenshots/tutor-new.png)

Tutors are the accounts for each tutor. Email is the gmail account the tutor uses to log in. The email is not editable once the tutor has been submitted! First Name and Last Name are the first and last names of the tutors. Is Active indicated is the tutor is currently employed. A tutor not marked as Is Active cannot login. Is Admin gives a tutor administrative rights. Currently Working marks a tutor as being present in the tutoring center right now. A currently working tutor is displayed on the course list under the classes they can tutor. The Can Tutor section is a checklist of the courses the tutor can tutor for.

Tutors are sorted by last name.

#### Reports

![Reports Page](screenshots/report.png)

The reports page contains a summary of all of the tickets in the system. The reports can be accessed when logged in as an administrator by clicking `Admin` in the toolbar, followed by `Reports`. If the `Admin` option does not exist you are not logged in as an administrator.

Various filters can be applied to the list. By entering a start date only tickets opened on or after the date will be displayed. By entering an end date only tickets opened on or before the date will be displayed. By selecting a semester only tickets that belong to that semester will be displayed. By selecting a course only tickets that belong to that course will be displayed. Once he desired filters are entered clicking the `Filter` button will apply them to the list.

##### Download Report

The current report can be downloaded in a CSV format (openable in Microsoft Excel) by clicking the `Download Report` button. The current list of tickets will be downloaded with the same filters applied. Filters are only applied to the download if they have been applied to the list using the `Filter` button.

##### Ticket Details

![Ticket Details Page](screenshots/ticket-details.png)

More information about a given ticket can be viewed by clicking the `Details` button on that ticket's row. Clicking the `Delete` button at the bottom of the details page will permanently delete the ticket.

## Appendix A. Setup and Installation

1. Install [Python 3](https://www.python.org/)
    1. The application must be run using Python 3
2. Run `pip3 install -r requirements.txt` (make sure you are using the version of pip for python3)
    1. If any modules fail to install they may have to be installed manually
    2. DBAPI modules for databases other than SQLite or PostgreSQL will have to be installed separately
3. Setup a Google API for the login system
    1. <https://console.developers.google.com/apis/credentials>
    2. Under credentials, create credentials for an OAuth Client ID
    3. Select Web application
    4. Provide the domain the application will run at, followed by `/oauth-authorized` (eg. `www.example.com/oauth-authorized`) as the authorized redirect URI
    5. Save the client ID and secret for later
<!-- 4. Setup a Google reCAPTCHA key/secret
    1. <https://www.google.com/recaptcha/admin>
    2. Select "invisible reCAPTCHA"
    3. Provide the domain (no subpage this time)
    4. Save the site key and secret key for later -->
5. Run `flask run -h 0.0.0.0 -p $PORT` where `$PORT` is the port you wish to run the server on (defaults to 5000) to create the appropriate database tables
    1. The `FLASK_APP` environment variable must be set to `application.py`
    2. The `FLASK_DEBUG` environment variable should be set to `0` unless you are testing the application (do not run in debug mode in a production environment)
    3. The database is specified in the `DB` environment variable
        * If the database is not a sqlite database, a SQLAlchemy dialect and DBAPI module may be required
        * See [this page](http://docs.sqlalchemy.org/en/latest/dialects/) for details about SQLAlchemy dialects and DBAPIs
        * The database URI must include the database dialect (eg. `postgresql://user:pass@localhost/test` would be a postgres database)
6. Access the database manually to add configuration information
    1. In the configuration table the Google API client ID from earlier goes in the setting column of the row with the name `GOOGLE_CONSUMER_KEY`
    2. Also in configuration, the Google API client secret goes in the setting column of the row with the name `GOOGLE_CONSUMER_SECRET`
    <!-- 3. Add the reCAPTCHA site key to the configuration in the `GOOGLE_CAPTCHA_KEY` row
    4. Add the reCAPTCHA secret key to the configuration in the `GOOGLE_CAPTCHA_SECRET` row -->
    5. In the tutors table create a tutor with an email you can log into Microsoft with. Set the `tutor_is_active` and `tutor_is_superuser` columns to true
7. Run portal.py again with the new configuration to start the site
8. By logging in as an administrator account other objects can be created
