#!/usr/bin/env python3

import enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Date,
    Enum,
    ForeignKey,
)
from sqlalchemy.schema import Table
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import cast

EMAIL = String(256)


class Base:
    def dict(self):
        '''
        Returns a dict of the object
        Primarily for json serialization
        '''
        return {c.key: getattr(self, c.key)
                for c in self.__mapper__.column_attrs}


Base = declarative_base(cls=Base)

cascade = "CASCADE"
null = "SET NULL"
noact = "NO ACTION"
onupdate = cascade
ondelete = noact

# Join table for the courses that tutors can help with
can_tutor_table = Table(
    'can_tutor',
    Base.metadata,
    Column(
        'tutor_id', Integer,
        ForeignKey('tutors.tutor_id', onupdate=onupdate, ondelete=cascade),
        primary_key=True,
        doc='The tutor for a course'),
    Column(
        'course_id', Integer,
        ForeignKey('courses.course_id', onupdate=onupdate, ondelete=cascade),
        primary_key=True,
        doc='The course that a tutor can tutor'),
)


class Config (Base):
    r"""
    Stores the configuration values for the application in key value pairs
    """
    __tablename__ = 'configuration'

    name = Column(
        String(64),
        primary_key=True,
        doc="The setting's name")
    value = Column(
        'setting', String,
        doc="The setting's value")


class Messages (Base):
    r"""
    Stores the messages to be displayed on the status screen
    """
    __tablename__ = 'messages'

    id = Column(
        'message_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    message = Column(
        'message_text', String,
        doc='The text to display on the status screen')
    start_date = Column(
        Date,
        doc='The beginning of when the message should be displayed')
    end_date = Column(
        Date,
        doc='The end of when the message should be displayed')

    def __str__(self):
        return self.message[:self.message.find('\n')]


class Status (Enum):
    r"""
    The status of a ticket
    """
    Open = 1
    Claimed = 2
    Closed = 3


class Tickets (Base):
    r"""
    Tickets requested by students
    Records the details of a tutoring session
    """
    __tablename__ = 'tickets'

    id = Column(
        'ticket_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    # Student information is not broken out into another table
    # to avoid having to create student accounts
    # (would be inefficient and impossible for non-UNO students)
    student_email = Column(
        EMAIL,
        nullable=False,
        doc='The email of the student requestig tutoring')
    student_fname = Column(
        String,
        doc='The first name of the student requesting tutoring')
    student_lname = Column(
        String,
        doc='The last name of the student requesting tutoring')
    student_fullname = column_property(student_fname + " " + student_lname)
    student_last_first = column_property(student_lname + " " + student_fname)
    assignment = Column(
        'ticket_assignment', String,
        doc='The assignment number the student needs help with')
    question = Column(
        'ticket_question', String,
        doc="The student's question about the assignment")
    status = Column(
        'ticket_status', Status,
        doc='The ticket status')
    time_created = Column(
        'ticket_time_created', DateTime(True),
        nullable=False,
        doc='Time the student requested tutoring')
    time_closed = Column(
        'ticket_time_closed', DateTime(True),
        doc='Time a tutor marked the ticket as closed')
    session_duration = Column(
        'ticket_session_duration', Integer,
        doc='The amount of time the tutors actually spent with the student')
    was_successful = Column(
        'ticket_was_successful', Boolean,
        doc='Whether the tutor thought the session was successful')
    tutor_id = Column(
        'tutor_id', Integer,
        ForeignKey('tutors.tutor_id', onupdate=noact, ondelete=ondelete),
        doc='The tutor that helped the student')
    assistant_tutor_id = Column(
        'assistant_tutor_id', Integer,
        ForeignKey('tutors.tutor_id', onupdate=noact, ondelete=ondelete),
        doc='The assisting tutor (if any)')
    section_id = Column(
        Integer,
        ForeignKey(
            'sections.section_id',
            onupdate=onupdate, ondelete=ondelete),
        nullable=False,
        doc="The class section the student needs help with")
    problem_type_id = Column(
        Integer,
        ForeignKey(
            'problem_types.problem_type_id',
            onupdate=onupdate, ondelete=ondelete),
        doc='The type of problem the student is having')

    tutor = relationship(
        'Tutors',
        foreign_keys=[tutor_id],
        back_populates='tickets')
    assistant_tutor = relationship(
        'Tutors',
        foreign_keys=[assistant_tutor_id],
        back_populates='assisted_tickets')
    section = relationship(
        'Sections',
        back_populates='tickets')
    problem_type = relationship(
        'ProblemTypes',
        back_populates='tickets')

    def dict(self):
        return {
            'id': self.id,
            'name': self.fname,
            'course': '{}-{:03}'.format(
                self.section.course.number,
                self.section.number
            ),
            'assignment': self.assignment,
            'question': self.question,
        }

    def __str__(self):
        return ' | '.join(map(str, [
            self.student_fullname,
            self.course,
            self.assignment,
            self.question,
        ]))

    @property
    def course_number(self):
        return '{}-{:03}'.format(
            self.section.course.number,
            self.section.number,
        )


class ProblemTypes (Base):
    r"""
    The types of problems that students can specify when creating a ticket
    """
    __tablename__ = 'problem_types'

    id = Column(
        'problem_type_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    description = Column(
        'problem_type_description', String,
        nullable=False,
        doc='The description of the problem type')

    tickets = relationship(
        'Tickets',
        order_by='Tickets.id',
        back_populates='problem_type')

    def __str__(self):
        return self.description


class Tutors (Base):
    r"""
    The login information for tutors
    Also allows tickets to specify a tutor and assisting tutor
    """
    __tablename__ = 'tutors'

    id = Column(
        'tutor_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    email = Column(
        'tutor_email', EMAIL,
        unique=True,
        doc="The tutor's UNO email")
    fname = Column(
        'tutor_fname', String,
        doc="The tutor's first name")
    lname = Column(
        'tutor_lname', String,
        doc="The tutor's last name")
    is_active = Column(
        'tutor_is_active', Boolean,
        doc='If the tutor is currently employed')
    is_superuser = Column(
        'tutor_is_superuser', Boolean,
        doc='If the tutor has administrator privileges')
    is_working = Column(
        'tutor_is_working', Boolean,
        doc='If the tutor is currently working')
    fullname = column_property(fname + " " + lname)
    last_first = column_property(lname + ", " + fname)

    tickets = relationship(
        'Tickets',
        foreign_keys=[Tickets.tutor_id],
        order_by='Tickets.id',
        back_populates='tutor')
    assisted_tickets = relationship(
        'Tickets',
        foreign_keys=[Tickets.assistant_tutor_id],
        order_by='Tickets.id',
        back_populates='assistant_tutor')
    courses = relationship(
        'Courses',
        secondary=can_tutor_table,
        order_by='Courses.number',
        back_populates='tutors')

    def __str__(self):
        return '{}: {}'.format(self.last_first, self.email)


class Courses (Base):
    r"""
    The courses available for tutoring
    """
    __tablename__ = 'courses'

    id = Column(
        'course_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    number = Column(
        'course_number', String,
        nullable=False,
        doc='The course number eg. CIST 1400')
    name = Column(
        'course_name', String,
        doc='The course name eg. Java I')
    on_display = Column(
        'course_on_display', Boolean,
        doc='If the course should appear on the status list')

    sections = relationship(
        'Sections',
        order_by='Sections.number',
        back_populates='course')
    tutors = relationship(
        'Tutors',
        secondary=can_tutor_table,
        order_by='Tutors.fullname',
        back_populates='courses')

    def __str__(self):
        return '{}: {}'.format(self.number, self.name)


class Sections (Base):
    r"""
    The sections of the various courses offered during a given semester
    """
    __tablename__ = 'sections'

    id = Column(
        'section_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    number = Column(
        'section_number', Integer,
        nullable=False,
        doc='The section number eg. 001')
    time = Column(
        'section_time', String,
        doc="The course's time eg. MW 9:00AM")
    course_id = Column(
        Integer,
        ForeignKey('courses.course_id', onupdate=onupdate, ondelete=ondelete),
        nullable=False,
        doc='The course the section belongs to')
    semester_id = Column(
        Integer,
        ForeignKey(
            'semesters.semester_id',
            onupdate=onupdate, ondelete=ondelete),
        doc='The semester a section occurs during')
    professor_id = Column(
        Integer,
        ForeignKey(
            'professors.professor_id',
            onupdate=onupdate, ondelete=ondelete),
        doc='The professor that teaches a section')

    tickets = relationship(
        'Tickets',
        order_by='Tickets.id',
        back_populates='section')
    course = relationship(
        'Courses',
        lazy='joined',
        back_populates='sections')
    semester = relationship(
        'Semesters',
        lazy='joined',
        back_populates='sections')
    professor = relationship(
        'Professors',
        lazy='joined',
        back_populates='sections')

    def __str__(self):
        s = []
        if self.course and self.number:
            s.append('{}-{:03}'.format(self.course.number, self.number))
        elif self.course:
            s.append(self.course.number)
        elif self.number:
            s.append('{:03}'.format(self.number))
        if self.time:
            s.append(self.time)
        if self.professor and self.professor.lname:
            s.append(self.professor.lname)
        if self.semester:
            s.append(str(self.semester))

        if s:
            s = ', '.join(s)
        else:
            s = str(self.id)

        return s


class Professors (Base):
    r"""
    The professors teaching various class sections
    """
    __tablename__ = 'professors'

    id = Column(
        'professor_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    fname = Column(
        'professor_fname', String,
        nullable=False,
        doc="The professor's first name")
    lname = Column(
        'professor_lname', String,
        nullable=False,
        doc="The professor's last name")
    fullname = column_property(fname + " " + lname)
    last_first = column_property(lname + ", " + fname)

    sections = relationship(
        'Sections',
        order_by='Sections.number',
        back_populates='professor')

    def __str__(self):
        return self.last_first


class Seasons (Enum):
    r"""
    The valid seasons for a semester
    """
    Spring = 1
    Summer = 2
    Fall = 3

    def list():
        out = dict()
        out[1] = 'Spring'
        out[2] = 'Summer'
        out[3] = 'Fall'
        return out

class Semesters (Base):
    r"""
    The semesters that course sections can occur during
    """
    __tablename__ = 'semesters'

    id = Column(
        'semester_id', Integer,
        primary_key=True,
        doc='An autonumber id')
    year = Column(
        'semester_year', Integer,
        nullable=False,
        doc='The year of a semester')
    season = Column(
        'semester_season', Seasons,
        nullable=False,
        doc='The season of a semester')
    start_date = Column(
        'semester_start_date', Date,
        nullable=False,
        doc='The first day of the semester')
    end_date = Column(
        'semester_end_date', Date,
        nullable=False,
        doc='The last day of the semester')
    title = column_property(cast(year, String) + ' ' + season)

    sections = relationship(
        'Sections',
        order_by='Sections.number',
        back_populates='semester')

    def __str__(self):
        return '{} {:04}'.format(self.season.name, self.year)


if __name__ == '__main__':
    from operator import attrgetter

    for table in sorted(Base.metadata.tables.values(), key=attrgetter('name')):
        print(table.name)
        for column in table.columns:
            col = '{}: {}'.format(column.name, column.type)

            if column.primary_key and column.foreign_keys:
                col += ' PK & FK'
            elif column.primary_key:
                col += ' PK'
            elif column.foreign_keys:
                col += ' FK'

            if not column.nullable:
                col += ' NOT NULL'

            doc = column.doc
            if isinstance(column.type, Enum):
                doc += ': ' + ', '.join(
                    column.type.python_type.__members__.keys())
            print('\t{}\n\t\t{}'.format(col, doc))
        print()
