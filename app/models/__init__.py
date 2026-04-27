from app import db

###
#
# ✅ MAJOR # Carrera
#
###
class Major(db.Model):
    __tablename__ = 'majors'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    
    # Relationship to easily access all students enrolled in this major
    students = db.relationship('Student', backref='major', lazy=True)

    def __str__(self):
        return f"Major: {self.code}, Name: {self.name}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

###
#
# ✅ STUDENT
#
###
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    identification = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)

    # Foreign key linking the student to their major
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False)
    
    # Relationship to retrieve all grades associated with this student
    grades = db.relationship('Grade', backref='student', lazy=True)

    def __str__(self):
        return f"Student: {self.identification}, Name: {self.name}"

    def to_dict(self):
        return {
            'id': self.id,
            'identification': self.identification,
            'name': self.name
        }

###
#
# ✅ SUBJECT # Asignatura
#
###
class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)

    def __str__(self):
        return f"Subject: {self.code}, Name: {self.name}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

###
#
# ✅ ACADEMIC PERIOD # Periodo Academico
#
###
class AcademicPeriod(db.Model):
    __tablename__ = 'academic_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    
    def __str__(self):
        return f"Academic Period: {self.code}"

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code
        }

###
#
# ✅ GRADE # Nota
#
###
class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    final_score = db.Column(db.String(20), nullable=False) # String because it can be "No Presento"
    condition = db.Column(db.String(20)) # e.g., 'RG', 'RP'
    
    # Foreign keys linking to the specific student and subject
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    academic_period_id = db.Column(db.Integer, db.ForeignKey('academic_periods.id'), nullable=True)
    
    # Relationship for easy access to the subject and academic period
    subject = db.relationship('Subject')
    academic_period = db.relationship('AcademicPeriod')

    def __str__(self):
        return f"Grade: {self.final_score}, Condition: {self.condition}"

    def to_dict(self):
        return {
            'id': self.id,
            'final_score': self.final_score,
            'condition': self.condition,
            'student_id': self.student_id,
            'subject_id': self.subject_id,
            'academic_period_id': self.academic_period_id
        }