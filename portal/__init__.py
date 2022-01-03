#!/usr/bin/env python3

import sys
import os
import datetime
import csv
import io
from operator import attrgetter

import pytz
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    Response,
    send_from_directory,
    session,
    url_for,
)
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager, selectinload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask_sqlalchemy import SQLAlchemy, _QueryProperty
from flask_oauthlib.client import OAuth
import requests
import bleach
import markdown2
from O365 import Account
from . import revproxy
from . import model as m
# Default ordering for admin types
m.Semesters.order_by = m.Semesters.start_date.desc()
m.Professors.order_by = m.Professors.last_first
m.Courses.order_by = m.Courses.number
m.Sections.order_by = m.Sections.number
m.ProblemTypes.order_by = m.ProblemTypes.description
m.Messages.order_by = m.Messages.end_date.desc()

# Create App
app = Flask(__name__)
app.wsgi_app = revproxy.ReverseProxied(app.wsgi_app,"",'https')
api = Api(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.environ['DB']
# Attach Database
db = SQLAlchemy(app)
db.Model = m.Base
# Ugly code to make Base.query work
m.Base.query_class = db.Query
m.Base.query = _QueryProperty(db)
# Configure Google OAuth
# oauth = OAuth()
# google = oauth.remote_app(
#     'google',
#     app_key='GOOGLE',
#     request_token_params={'scope': 'email'},
#     base_url='https://www.googleapis.com/oauth2/v1/',
#     request_token_url=None,
#     access_token_method='POST',
#     access_token_url='https://accounts.google.com/o/oauth2/token',
#     authorize_url='https://accounts.google.com/o/oauth2/auth',
# )




# bleach config
BLEACH_ALLOWED_TAGS = [
    # default tags
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'pre',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
    # markdown tags
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'p',
    'table',
    'thead',
    'tbody',
    'tr',
    'th',
    'td',
    'img',
    'hr',
    'br',
    'div',
    'section',
    'article',
    'span',
]
BLEACH_ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
    'img': ['src', 'alt', 'title'],
    'td': ['align'],
    'th': ['align'],
}
BLEACH_ALLOWED_STYLES = [
    'color',
    'text-align',
]


@app.before_first_request
def create_app():
    r"""
    Sets up app for use
    Adds database configuration and the secret key
    """
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # setup config values
    with app.app_context():
        # setup Database
        db.create_all()
        # these settings are stored in the configuration table
        # values here are defaults (and should all be strings or null)
        # defaults will autopopulate the database when first initialized
        # when run subsequently, they will be populated from the database
        # only populated on startup, changes not applied until restart
        config = {
            # key used to encrypt cookies
            'SECRET_KEY': os.urandom(24),

            # cookie lifetime in minutes, unused
            'PERMANENT_SESSION_LIFETIME': '30',

            # Google OAth client ID
            'GOOGLE_CONSUMER_KEY': None,

            # Google OAuth client secret
            'GOOGLE_CONSUMER_SECRET': None,

            # Google CAPTCHA site key
            'GOOGLE_CAPTCHA_KEY': None,

            # Google CAPTCHA secret key
            'GOOGLE_CAPTCHA_SECRET': None,

            # Timezone configuration,
            # determines how times are displayed to users
            # timestamps are always stored in UTC
            # uses pytz timezone names
            'TZ_NAME': 'America/Chicago',

            # number of items on each page for reports
            'PAGE_LENGTH': '100',
        }
        # get Config values from database
        for name in config:
            try:
                key = m.Config.query.filter_by(name=name).one()
                config[name] = key.value
            except NoResultFound:
                key = m.Config(name=name, value=config[name])
                db.session.add(key)
                db.session.commit()

        config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
            minutes=int(config['PERMANENT_SESSION_LIFETIME']))
        config['PAGE_LENGTH'] = int(config['PAGE_LENGTH'])
        app.config.update(config)
        try:
            app.config['TZ'] = pytz.timezone(app.config['TZ_NAME'])
        except pytz.exceptions.UnknownTimeZoneError:
            sys.stderr.write('Unknown timzeone: "{}". Using UTC instead.\n'.format(
                app.config.get('TZ_NAME')
            ))


def make_safe(html):
    r"""
    Uses the bleach module to clean an HTML string
    Helps prevent javascript injection
    """
    return bleach.clean(
        html,
        tags=BLEACH_ALLOWED_TAGS,
        attributes=BLEACH_ALLOWED_ATTRIBUTES,
        styles=BLEACH_ALLOWED_STYLES,
        strip_comments=False,
    )


def markdown(md):
    r"""
    Outputs safe markdown using the markdown2 and bleach modules
    """
    html = markdown2.markdown(md, html4tags=True, extras=[
        'cuddled-lists',
        'fenced-code-blocks',
        'footnotes',
        'markdown-in-html',
        'tables',
        'tag-friendly',
        'target-blank-links',
    ])
    return make_safe(html)


def correct_time(time):
    r"""
    Takes a datetime object and returns that time
        corrected for the appropriate timezone
    """
    if time is not None:
        timezone = app.config.get('TZ')
        if timezone is not None:
            time = time.astimezone(timezone)
    return time


def now():
    r"""
    Gets the current time in the America/Chicago timezone
    """
    UTC = datetime.timezone.utc
    now = datetime.datetime.now(UTC)
    return now


def now_today():
    r"""
    Returns a date corrected for the selected timezone
    """
    return correct_time(now()).date()


def date(string):
    r"""
    Convert a date formated string to a date object
    """
    if string == '':
        return None
    else:
        return datetime.datetime.strptime(string, '%Y-%m-%d').date()


def get_int(string):
    r"""
    Convert a string to int, returning None for invalid strings
    """
    ret = None
    if string is not None:
        try:
            ret = int(string)
        except ValueError:
            pass
    return ret


def get_str(string):
    r"""
    Converts a string to a string, returning None for empty strings
    """
    return None if string == '' else string


@app.context_processor
def context():
    r"""
    Makes extra variables available to the template engine
    """
    return dict(
        m=m,
        str=str,
        int=get_int,
        date=date,
        len=len,
        markdown=markdown,
        correct_time=correct_time,
    )


def error(e, message):
    r"""
    Basic error template for all error pages
    """
    try:
        user = get_user()
    except:  # noqa: E722
        user = None

    html = render_template(
        'error.html',
        title=str(e),
        message=message,
        user=user,
    )
    return html


@app.errorhandler(403)
def four_oh_three(e):
    r"""
    403 (forbidden) error page
    """
    return error(e, "You don't have access to this page."), 403


@app.errorhandler(404)
def four_oh_four(e):
    r"""
    404 (page not found) error page
    """
    return error(e, "We couldn't find the page you were looking for."), 404


@app.errorhandler(500)
def five_hundred(e):
    r"""
    500 (internal server) error page
    """
    if isinstance(e, NoResultFound):
        message = 'Could not find the requested item in the database.'
    elif isinstance(e, MultipleResultsFound):
        message = 'Found too many results for the requested resource.'
    elif isinstance(e, IntegrityError):
        message = 'Invalid data entered. '
        message += 'Either a duplicate record was entered or '
        message += 'not all fields were filled out.'
    else:
        message = 'Whoops, looks like something went wrong!'
    return error('500: ' + type(e).__name__, message), 500


def get_user():
    r"""
    Gets the user data from the current session
    Returns the Tutor object of the current user
    """
    email = session.get('username')
    user = None
    if email:
        if app.debug:
            user = m.Tutors(email=email, is_active=True, is_superuser=True)
        else:
            try:
                user = m.Tutors.query.filter_by(email=email).one()
            except NoResultFound:
                session.clear()
                flash('&#10006; User does not exist: {}.'.format(email))

        if user and not user.is_active:
            session.clear()
            flash('&#10006; User is not active: {}.'.format(email))
            user = None
    return user


@app.route('/favicon.ico')
def favicon():
    r"""
    The favorites icon for the site
    """
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )


# ----#-   Pages
@app.route('/')
def index():
    r"""
    The home page, from which tutors can login and students can open tickets
    """
    user = get_user()
    html = render_template(
        'index.html',
        home=True,
        user=user,
    )
    return html


@app.route('/status.html')
def status():
    r"""
    A status page for the CSLC
    For students displays:
        Annoucements
        Course Availability
    For tutors, also displays:
        Open Tickets
    """
    user = get_user()

    html = render_template(
        'status.html',
        user=user,
    )
    return html


@api.resource('/api/messages')
class Messages (Resource):
    '''
    List of messages to display on the status screen
    '''
    def get(self):
        today = now_today()
        tomorrow = today + datetime.timedelta(days=1)

        messages = m.Messages.query.filter(
            (
                (m.Messages.start_date <= tomorrow) |
                (m.Messages.start_date.is_(None))
            ) &
            (
                (m.Messages.end_date >= today) |
                (m.Messages.end_date.is_(None))
            )
        ).order_by(m.Messages.order_by).all()

        return list(map(lambda a: markdown(a.message), messages))


@api.resource('/api/courses')
class Courses (Resource):
    '''
    Course table with name, current tickets, and current tutors for each course
    '''
    def get(self):
        courses = m.Courses.query.\
            order_by(m.Courses.order_by).\
            filter(m.Courses.on_display == True).\
            all()

        for course in courses:
            course.current_tickets = m.Tickets.query.filter(
                m.Tickets.status.in_((None, m.Status.Open, m.Status.Claimed))
            ).join(m.Sections).filter_by(course=course).count()

            course.current_tutors = m.Tutors.query.\
                filter_by(is_working=True).\
                join(m.can_tutor_table).\
                filter(course.id == m.can_tutor_table.columns['course_id']).count()

        other_tickets = m.Tickets.query.\
            filter(m.Tickets.status.in_((None, m.Status.Open, m.Status.Claimed))).\
            join(m.Sections).\
            filter(~m.Sections.course_id.in_(map(attrgetter('id'), courses))).\
            count()

        courses = list(map(lambda a: {
            'name': str(a),
            'current_tickets': a.current_tickets,
            'current_tutors': a.current_tutors,
        }, courses))
        courses.extend([
            {
                'name': 'Other',
                'current_tickets': other_tickets,
                'current_tutors': '-',
            },
            {
                'name': 'Total',
                'current_tickets': sum(c['current_tickets'] for c in courses) + other_tickets,
                'current_tutors': m.Tutors.query.filter_by(is_working=True).count(),
            }
        ])
        return courses


def get_open_courses():
    r"""
    Gets a list of courses and sections for the current semester
    """
    today = now_today()
    tomorrow = today + datetime.timedelta(days=1)
    return m.Courses.query.join(m.Sections).join(m.Semesters).\
        order_by(m.Courses.number).\
        order_by(m.Sections.number).\
        filter(m.Semesters.start_date <= tomorrow).\
        filter(m.Semesters.end_date >= today).\
        options(contains_eager(m.Courses.sections)).\
        all()


@app.route('/open_ticket/')
def open_ticket():
    r"""
    The student page for opening a ticket
    """
    user = get_user()

    courses = get_open_courses()
    problems = m.ProblemTypes.query.order_by(m.ProblemTypes.order_by).all()

    html = render_template(
        'edit_open_ticket.html',
        user=user,
        courses=courses,
        problems=problems,
    )
    return html


@app.route('/open_ticket/', methods=['POST'])
def save_open_ticket():
    r"""
    Creates a new ticket and stores it in the database
    """
    # https = requests.post(
    #     'https://www.google.com/recaptcha/api/siteverify',
    #     data={
    #         'secret': app.config['GOOGLE_CAPTCHA_SECRET'],
    #         'response': request.form.get('g-recaptcha-response'),
    #     },
    # )
    # verification = https.json()

    # if not verification.get('success'):
    #     flash('&#10006; Invalid CAPTCHA response')
    #     return redirect(url_for('index'))

    ticket_form = {
        'student_email': get_str,
        'student_fname': get_str,
        'student_lname': get_str,
        'section_id': get_int,
        'assignment': get_str,
        'question': get_str,
        'problem_type_id': get_int,
    }

    form = {}
    for key, value in ticket_form.items():
        form[key] = value(request.form.get(key))

    form['status'] = m.Status.Open
    form['time_created'] = now()

    ticket = m.Tickets(**form)
    db.session.add(ticket)
    db.session.commit()

    flash('&#10004; Ticket successfully opened')
    return redirect(url_for('index'))


@app.route('/tickets/')
def view_tickets():
    r"""
    View/Claim/Close tickets
    """
    user = get_user()
    if not user:
        return redirect(url_for('login', next=url_for('view_tickets')))

    today = now_today()
    tickets = m.Tickets.query.order_by(m.Tickets.time_created).\
        join(m.Sections).\
        join(m.Semesters).\
        join(m.Courses).\
        filter(
            (m.Tickets.time_created >= today) |
            (m.Tickets.time_closed >= today) |
            (m.Tickets.status.in_((None, m.Status.Open, m.Status.Claimed)))).\
        all()

    open = []
    claimed = []
    closed = []
    for ticket in tickets:
        if ticket.status in (None, m.Status.Open):
            open.append(ticket)
        elif ticket.status == m.Status.Claimed:
            claimed.append(ticket)
        elif ticket.status == m.Status.Closed:
            closed.append(ticket)
        else:
            raise ValueError('Invalid ticket status: {}'.format(ticket.status))

    html = render_template(
        'list_tickets.html',
        user=user,
        open=open,
        claimed=claimed,
        closed=closed,
    )
    return html


@app.route('/tickets/close/<id>')
def close_ticket(id):
    r"""
    The tutor page for claiming and closing tickets
    """
    user = get_user()
    if not user:
        return abort(403)

    ticket = m.Tickets.query.filter_by(id=id).one()
    courses = get_open_courses()
    problems = m.ProblemTypes.query.order_by(m.ProblemTypes.order_by).all()
    tutors = m.Tutors.query.\
        filter_by(is_active=True).\
        order_by(m.Tutors.last_first).\
        all()

    html = render_template(
        'edit_close_ticket.html',
        user=user,
        ticket=ticket,
        courses=courses,
        problems=problems,
        tutors=tutors,
    )
    return html


@app.route('/tickets/close/', methods=['POST'])
def save_close_ticket():
    r"""
    Saves changes to a ticket into the database
    """
    user = get_user()
    if not user:
        return abort(403)

    close_ticket_form = {
        'assignment': get_str,
        'question': get_str,
        'session_duration': get_int,
        'was_successful': bool,
        'tutor_id': get_str,
        'assistant_tutor_id': get_str,
        'section_id': get_int,
        'problem_type_id': get_int,
    }

    form = {}
    for key, value in close_ticket_form.items():
        form[key] = value(request.form.get(key))

    if request.form.get('submit') == 'claim':
        form['status'] = m.Status.Claimed
    elif request.form.get('submit') == 'close':
        form['status'] = m.Status.Closed
        form['time_closed'] = now()
    else:
        raise ValueError('Invalid submit type: {}'.format(form.get('submit')))

    id = get_int(request.form.get('id'))
    ticket = m.Tickets.query.filter_by(id=id).one()

    for key, value in form.items():
        if getattr(ticket, key) != value:
            setattr(ticket, key, value)
    db.session.commit()

    html = redirect(url_for('view_tickets'))
    return html


@app.route('/tickets/reopen/<id>')
def reopen_ticket(id):
    r"""
    Moves a ticket from closed to claimed
    """
    user = get_user()
    if not user:
        return abort(403)

    ticket = m.Tickets.query.filter_by(id=id).one()
    ticket.status = m.Status.Claimed
    db.session.commit()

    return redirect(url_for('view_tickets'))


@app.route('/workinglist')
def working_list():
    r"""
    Displays and allows editing of the working status of tutors
    """
    user = get_user()
    if not user:
        return abort(403)

    items = m.Tutors.query.\
        filter_by(is_active=True).\
        order_by(m.Tutors.is_working.desc()).\
        order_by(m.Tutors.last_first).\
        all()

    html = render_template(
        'working.html',
        user=user,
        items=items,
    )
    return html


@app.route('/workinglist', methods=['POST'])
def submit_working():
    r"""
    Sets the list of tutors that are and are not working
    """
    user = get_user()
    if not user:
        return abort(403)

    tutors = m.Tutors.query.filter_by(is_active=True).all()

    for tutor in tutors:
        tutor.is_working = bool(request.form.get(str(tutor.id), False))

    db.session.commit()

    html = redirect(url_for('working_list'))
    return html


@app.route('/deactivatetutors')
def deactivate_tutors():
    r"""
    Sets all tutors to inactive and redirects to the tutor list
    """
    user = get_user()
    if not user:
        return abort(403)

    m.Tutors.query.update({m.Tutors.is_working: False})
    db.session.commit()

    html = redirect(url_for('working_list'))
    return html


# ----#-   Administration tools
def filter_report(args):
    r"""
    Filters reports by query arguments
    """
    tickets = m.Tickets.query.\
        order_by(m.Tickets.time_created.desc()).\
        join(m.Sections)

    if args.get('min_date', ''):
        min_date = date(args['min_date'])
        tickets = tickets.filter(m.Tickets.time_created >= min_date)
    if args.get('max_date', ''):
        max_date = date(args['max_date']) + datetime.timedelta(days=1)
        tickets = tickets.filter(m.Tickets.time_created <= max_date)

    if args.get('semester', ''):
        semester = get_int(args['semester'])
        tickets = tickets.filter(m.Sections.semester_id == semester)

    if args.get('course', ''):
        course = get_int(args['course'])
        tickets = tickets.filter(m.Sections.course_id == course)

    return tickets


@app.route('/reports/')
def reports():
    r"""
    The report page for the administrator
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    limit = app.config['PAGE_LENGTH']
    page = get_int(request.args.get('page'))
    if page is None:
        page = 1
    offset = (page - 1) * limit

    items = filter_report(request.args)
    numItems = items.count()
    items = items.limit(limit).offset(offset).all()
    semesters = m.Semesters.query.order_by(m.Semesters.order_by).all()
    courses = m.Courses.query.order_by(m.Courses.order_by).all()

    maxPage = ((numItems - 1) // limit) + 1
    if maxPage < 1:
        maxPage = 1

    args = dict(request.args)
    if 'page' in args:
        args.pop('page')

    html = render_template(
        'report.html',
        user=user,
        items=items,
        semesters=semesters,
        courses=courses,

        numItems=numItems,
        page=page,
        limit=limit,
        offset=offset,
        maxPage=maxPage,
        args=args,
    )
    return html


def fix_dde(cell):
    '''
    Handles a vulnerability with embedded formulae in csv files
    '''
    if cell is not None:
        cell = str(cell)
        if cell.startswith(('=', '+', '-', '@')):
            cell = "' " + cell
        cell = cell.rstrip()
    return cell


@app.route('/report/file/cslc_report.csv')
def report_download():
    r"""
    Downloads a report as a CSV
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    tickets = filter_report(request.args).\
        join(m.ProblemTypes).\
        join(m.Courses).\
        join(m.Semesters).\
        join(m.Professors).\
        options(
            selectinload(m.Tickets.tutor),
            selectinload(m.Tickets.assistant_tutor)).\
        all()

    headers = [
        'URL',
        'Student Email',
        'Student First Name',
        'Student Last Name',
        'Assignment',
        'Question',
        'Problem Type',
        'Status',
        'Time Created',
        'Time Closed',
        'Was Successful',
        'Primary Tutor',
        'Assistant Tutor',
        'Semester',
        'Course Number',
        'Section Number',
        'Professor',
    ]
    report = [headers]
    for ticket in tickets:
        ticket_url = url_for('ticket_details', id=ticket.id, _external=True)
        elem = [
            ticket_url,
            ticket.student_email,
            ticket.student_fname,
            ticket.student_lname,
            ticket.assignment,
            ticket.question,
            ticket.problem_type.description,
            ticket.status.name if ticket.status else 'Unknown',
            ticket.time_created or 'Unknown',
            ticket.time_closed or 'Not closed yet',
            ticket.was_successful,
            ticket.tutor or 'None',
            ticket.assistant_tutor or 'None',
            ticket.section.semester.title,
            ticket.section.course.number,
            ticket.section.number,
            ticket.section.professor.last_first,
        ]
        elem = map(fix_dde, elem)
        elem = list(elem)
        report.append(elem)

    file = io.StringIO()
    writer = csv.writer(file)
    for line in report:
        writer.writerow(line)
    return Response(
        file.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-disposition': 'attatchment; filename=cslc_report.csv',
        },
    )


@app.route('/reports/ticket/<int:id>')
def ticket_details(id):
    r"""
    Allows the administrator to view the details of a specific ticket
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    ticket = m.Tickets.query.filter_by(id=id).one()

    html = render_template(
        'ticket_details.html',
        user=user,
        ticket=ticket,
    )
    return html


@app.route('/reports/ticket/<int:id>/delete')
def delete_ticket(id):
    r"""
    Deletes a ticket from the database
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    obj = m.Tickets.query.filter_by(id=id).one()
    db.session.delete(obj)
    db.session.commit()

    return redirect(url_for('reports'))


@app.route('/admin/')
def admin():
    r"""
    The admin configutration page
    Can add professors, semesters, courses, sections, tutors, and more
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    html = render_template(
        'admin.html',
        user=user,
    )
    return html


@app.route('/admin/semesters/', defaults={'type': m.Semesters})
@app.route('/admin/professors/', defaults={'type': m.Professors})
@app.route('/admin/courses/', defaults={'type': m.Courses})
@app.route('/admin/sections/', defaults={'type': m.Sections})
@app.route('/admin/problems/', defaults={'type': m.ProblemTypes})
@app.route('/admin/messages/', defaults={'type': m.Messages})
def list_admin(type):
    r"""
    Displays and allows editing of the available admin objects
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    title = {
        m.Semesters: 'Semesters',
        m.Professors: 'Professors',
        m.Courses: 'Courses',
        m.Sections: 'Course Sections',
        m.ProblemTypes: 'Problem Types',
        m.Messages: 'Messages',
    }.get(type)

    limit = app.config['PAGE_LENGTH']
    page = get_int(request.args.get('page'))
    if page is None:
        page = 1
    offset = (page - 1) * limit

    items = type.query
    if type == m.Sections:
        items = items.join(m.Semesters)
        items = items.join(m.Courses)
        items = items.order_by(m.Semesters.order_by)
        items = items.order_by(m.Courses.order_by)
    items = items.order_by(type.order_by)
    numItems = items.count()
    items = items.limit(limit).offset(offset).all()

    maxPage = ((numItems - 1) // limit) + 1
    if maxPage < 1:
        maxPage = 1

    args = dict(request.args)
    if 'page' in args:
        args.pop('page')

    html = render_template(
        'list_admin.html',
        user=user,
        title=title,
        type=type,
        items=items,
        numItems=numItems,
        limit=limit,
        page=page,
        offset=offset,
        maxPage=maxPage,
        args=args,
    )
    return html


@app.route('/admin/semesters/new', defaults={'type': m.Semesters})
@app.route('/admin/professors/new', defaults={'type': m.Professors})
@app.route('/admin/courses/new', defaults={'type': m.Courses})
@app.route('/admin/sections/new', defaults={'type': m.Sections})
@app.route('/admin/problems/new', defaults={'type': m.ProblemTypes})
@app.route('/admin/messages/new', defaults={'type': m.Messages})
@app.route('/admin/semesters/<int:id>', defaults={'type': m.Semesters})
@app.route('/admin/professors/<int:id>', defaults={'type': m.Professors})
@app.route('/admin/courses/<int:id>', defaults={'type': m.Courses})
@app.route('/admin/sections/<int:id>', defaults={'type': m.Sections})
@app.route('/admin/problems/<int:id>', defaults={'type': m.ProblemTypes})
@app.route('/admin/messages/<int:id>', defaults={'type': m.Messages})
def edit_admin(type, id=None):
    r"""
    Allows editing and creation of admin objects
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    if id is None:
        obj = None
    else:
        obj = type.query.filter_by(id=id).one()

    html = render_template(
        'edit_%s.html' % type.__tablename__,
        user=user,
        type=type,
        obj=obj,
    )
    return html


semester_form = {
    'year': get_int,
    'season': lambda a: m.Seasons(int(a)),
    'start_date': date,
    'end_date': date,
}
professor_form = {
    'fname': get_str,
    'lname': get_str,
}
course_form = {
    'number': get_str,
    'name': get_str,
    'on_display': bool,
}
section_form = {
    'number': get_str,
    'time': get_str,
    'course_id': get_int,
    'semester_id': get_int,
    'professor_id': get_int,
}
problem_form = {
    'description': get_str,
}
message_form = {
    'message': get_str,
    'start_date': date,
    'end_date': date,
}


@app.route(
    '/admin/semesters/', methods=['POST'], defaults={'type': m.Semesters})
@app.route(
    '/admin/professors/', methods=['POST'], defaults={'type': m.Professors})
@app.route(
    '/admin/courses/', methods=['POST'], defaults={'type': m.Courses})
@app.route(
    '/admin/sections/', methods=['POST'], defaults={'type': m.Sections})
@app.route(
    '/admin/problems/', methods=['POST'], defaults={'type': m.ProblemTypes})
@app.route(
    '/admin/messages/', methods=['POST'], defaults={'type': m.Messages})
def save_edit_admin(type):
    r"""
    Handles changes to administrative objects
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    if request.form.get('action') == 'delete':
        obj = type.query.filter_by(id=request.form.get('id')).one()
        db.session.delete(obj)
    else:
        form = {
            m.Semesters: semester_form,
            m.Professors: professor_form,
            m.Courses: course_form,
            m.Sections: section_form,
            m.ProblemTypes: problem_form,
            m.Messages: message_form,
        }.get(type).copy()
        for key, value in form.items():
            form[key] = value(request.form.get(key))

        id = request.form.get('id')
        if id:
            obj = type.query.filter_by(id=id).one()
            for key, value in form.items():
                if getattr(obj, key) != value:
                    setattr(obj, key, value)
        else:
            obj = type(**form)
            db.session.add(obj)
    db.session.commit()

    html = redirect(url_for('list_admin', type=type))
    return html


@app.route('/admin/tutors/')
def list_tutors():
    r"""
    Displays and allows editing of the tutors
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    limit = app.config['PAGE_LENGTH']
    page = get_int(request.args.get('page'))
    if page is None:
        page = 1
    offset = (page - 1) * limit

    items = m.Tutors.query.\
        order_by(m.Tutors.is_active.desc()).\
        order_by(m.Tutors.is_working.desc()).\
        order_by(m.Tutors.is_superuser.desc()).\
        order_by(m.Tutors.last_first)
    numItems = items.count()
    items = items.limit(limit).offset(offset).all()

    maxPage = ((numItems - 1) // limit) + 1
    if maxPage < 1:
        maxPage = 1

    args = dict(request.args)
    if 'page' in args:
        args.pop('page')

    html = render_template(
        'list_tutors.html',
        user=user,
        header="Tutors",
        items=items,
        numItems=numItems,
        limit=limit,
        page=page,
        offset=offset,
        maxPage=maxPage,
        args=args,
    )
    return html


@app.route('/admin/tutors/new')
@app.route('/admin/tutors/<int:id>')
def edit_tutors(id=None):
    r"""
    Allows editing and creation of tutor objects
    """
    user = get_user()
    if not user or not (user.is_superuser or user.id == id):
        return abort(403)

    if id is None:
        tutor = None
    else:
        tutor = m.Tutors.query.filter_by(id=id).one()

    courses = m.Courses.query.\
        order_by(m.Courses.order_by).\
        filter(m.Courses.on_display == True).all()

    html = render_template(
        'edit_tutors.html',
        user=user,
        type=m.Tutors,
        obj=tutor,
        courses=courses,
    )
    return html


@app.route('/admin/tutors/', methods=['POST'])
def save_edit_tutors():
    r"""
    Handles changes to tutor objects
    """
    user = get_user()
    id = get_int(request.form.get('id'))
    if not user or not (user.is_superuser or user.id == id):
        return abort(403)

    if request.form.get('action') == 'delete':
        obj = type.query.filter_by(id=id).one()
        db.session.delete(obj)
    else:
        form = {
            'fname': get_str,
            'lname': get_str,
            'is_working': bool,
        }
        if user.is_superuser:
            form.update({
                'email': get_str,
                'is_active': bool,
                'is_superuser': bool,
            })
        for key, value in form.items():
            form[key] = value(request.form.get(key))

        if id is not None:
            obj = m.Tutors.query.filter_by(id=id).one()
            for key, value in form.items():
                if getattr(obj, key) != value:
                    setattr(obj, key, value)
        else:
            obj = m.Tutors(**form)
            db.session.add(obj)

        for course in m.Courses.query.all():
            if request.form.get(course.number):
                if course not in obj.courses:
                    obj.courses.append(course)
            else:
                if course in obj.courses:
                    obj.courses.remove(course)

    db.session.commit()

    if user.is_superuser:
        html = redirect(url_for('list_tutors'))
    else:
        html = redirect(url_for('index'))
    return html


# ----#-   Login/Logout
# @google.tokengetter
# def get_google_token(token=None):
#     r"""
#     Returns a user's token from OAuth
#     """
#     return session.get('google_token')


@app.route('/login/')
def login():
    r"""
    Redirects the user to the Google/UNO Single Sign On page
    Logs the user in as 'test@unomaha.edu' in debug mode
    """
    session.clear()
    # print('next : ' + request.args.get('next'))
    global next
    next = request.args.get('next') or request.referrer or None
    # if app.config['DEBUG']:
    #     session['username'] = 'test@unomaha.edu'
    #     session['google_token'] = (None, None)
    #     flash('&#10004; Successfully logged in as {}'.format(
    #         session.get('username')))
    #     html = redirect(next or url_for('index'))
    # else:
    #     html = google.authorize(
    #         callback=url_for('oauth_authorized', _external=True),
    #         state=next,
    #     )
    # callback = url_for('oauth_authorized')
    
    callback="https://68.106.214.90:5000" + url_for('oauth_authorized')
    account = Account((app.config['GOOGLE_CONSUMER_KEY'],app.config['GOOGLE_CONSUMER_SECRET']))


    myscopes=['https://graph.microsoft.com/email','https://graph.microsoft.com/offline_access','https://graph.microsoft.com/openid','https://graph.microsoft.com/profile','https://graph.microsoft.com/User.Read']
    url, Lstate= account.con.get_authorization_url(requested_scopes=myscopes,
                                                 redirect_uri=callback)

    return redirect(url)


@app.route('/oauth-authorized')
def oauth_authorized():
    r"""
    Logs the user in using the OAuth API
    """
    global next
    for x in request.args.keys():
        print(x + ' : ' + request.args.get(x))
    callback="https://68.106.214.90:5000" + url_for('oauth_authorized')
    next_url = next or url_for('index')
    account = Account((app.config['GOOGLE_CONSUMER_KEY'],app.config['GOOGLE_CONSUMER_SECRET']))

    result = account.con.request_token(request.url,
                                       state=request.args.get('state'),
                                       redirect_uri=callback)


    # resp = google.authorized_response()
    # if resp is None:
    #     return redirect(next_url)

    # session['google_token'] = (resp['access_token'], '')

    # https = requests.get(
    #     'https://www.googleapis.com/plus/v1/people/me',
    #     params={
    #         'access_token': session['google_token'][0],
    #         'fields': 'emails',
    #     },
    # )
    # userinfo = https.json()
    #
    # for email in userinfo.get('emails', []):
    #     if email['type'] == 'account':
    #         session['username'] = email['value']
    #         break
    #
    # if not m.Tutors.query.filter_by(email=session.get('username', '')).count():
    #     email = session.get('username')
    #     session.clear()


    userinfo = account.get_current_user().mail

    session['username'] = userinfo

    if not m.Tutors.query.filter_by(email=session.get('username', '')).count():
        email = session.get('username')
        print(email)
        session.clear()

    if result:
        flash('&#10004; Successfully logged in as ' + userinfo +'.')
        # print('Successfully logged in.')
        # for x in m.Seasons:
        #     print(x)
        # print(userinfo)
    else:
        flash('&#10006; Error logging in as ' + userinfo +'.')
        # print('Error logging in.')

    return redirect(next_url)


@app.route('/logout/')
def logout():
    r"""
    Logs the user out and returns them to the homepage
    """
    session.clear()
    flash(
        '&#10004; Successfully logged out. ' +
        'You will need to log out of Microsoft separately.')
    return redirect(url_for('index'))
# ----#-   End App

# if(os.environ['DB_DRIVER'] == 'mssql'):
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_DRIVER'] + 'mssql+pyodbc://' + os.environ['DB_USERNAME'] + ':' + os.environ['DB_PASSWORD'] + '@' + os.environ['DB_HOST'] + '/' + os.environ['DB_DATABASE'] + '?driver={FreeTDS}'
