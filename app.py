from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, fields


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Preciosa2016!@localhost/fitness_center_DB'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Models
class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(100))
    workout_sessions = db.relationship('WorkoutSession', backref='member')

class WorkoutSession(db.Model):
    __tablename__ = 'workout_sessions'
    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date, nullable=False)
    session_time = db.Column(db.String(50), nullable=False)
    activity = db.Column(db.String(100), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))

# Schemas
class MemberSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Member
        include_fk = True  # Include foreign key fields if needed

    id = ma.auto_field()
    name = fields.String(required=True)
    age = ma.auto_field()

member_schema = MemberSchema()
members_schema = MemberSchema(many=True)

class WorkoutSessionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = WorkoutSession
        include_fk = True

    id = ma.auto_field()
    session_date = fields.Date(required=True)
    session_time = ma.auto_field()
    activity = ma.auto_field()
    member_id = ma.auto_field()

workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

# Initialize the database and create tables
with app.app_context():
    db.create_all()

# ROUTES
# Get all members
@app.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify(members_schema.dump(members))

# Add a new member
@app.route('/members', methods=['POST'])
def add_member():
    try:
        # Validate and deserialize input
        member_data = member_schema.load(request.json)
        new_member = Member(
            name=member_data['name'],
            age=member_data.get('age')
        )
        db.session.add(new_member)
        db.session.commit()
        return jsonify({"message": "Member added successfully!"}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Update member
@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    try:
        # Retrieve the member by ID
        member = Member.query.get(id)
        if not member:
            return jsonify({"error": f"Member with id {id} not found."}), 404

        # Validate and deserialize input
        member_data = member_schema.load(request.json, partial=True)  # Allow partial updates

        # Update member attributes
        if 'name' in member_data:
            member.name = member_data['name']
        if 'age' in member_data:
            member.age = member_data['age']

        # Commit changes to the database
        db.session.commit()
        return jsonify({"message": f"Member with id {id} updated successfully."}), 200

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Delete member
@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    try:
        # Retrieve the member by ID
        member = Member.query.get(id)
        if not member:
            return jsonify({"error": f"Member with id {id} not found."}), 404

        # Delete the member
        db.session.delete(member)
        db.session.commit()
        return jsonify({"message": f"Member with id {id} deleted successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

###################################################
# Add a new workout session
@app.route('/workout_sessions', methods=['POST'])
def schedule_workout_session():
    try:
        # Validate and deserialize input
        session_data = workout_session_schema.load(request.json)
        new_session = WorkoutSession(
            session_date=session_data['session_date'],
            session_time=session_data['session_time'],
            activity=session_data['activity'],
            member_id=session_data['member_id']
        )
        # Check if member exists
        member = Member.query.get(session_data['member_id'])
        if not member:
            return jsonify({"error": f"Member with id {session_data['member_id']} not found."}), 404

        db.session.add(new_session)
        db.session.commit()
        return jsonify({"message": "Workout session scheduled successfully."}), 201

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Update an existing workout session
@app.route('/workout_sessions/<int:id>', methods=['PUT'])
def update_workout_session(id):
    try:
        session = WorkoutSession.query.get(id)
        if not session:
            return jsonify({"error": f"Workout session with id {id} not found."}), 404

        # Validate and deserialize input
        session_data = workout_session_schema.load(request.json, partial=True)

        # Update session attributes
        if 'session_date' in session_data:
            session.session_date = session_data['session_date']
        if 'session_time' in session_data:
            session.session_time = session_data['session_time']
        if 'activity' in session_data:
            session.activity = session_data['activity']
        if 'member_id' in session_data:
            # Check if the new member exists
            member = Member.query.get(session_data['member_id'])
            if not member:
                return jsonify({"error": f"Member with id {session_data['member_id']} not found."}), 404
            session.member_id = session_data['member_id']

        db.session.commit()
        return jsonify({"message": f"Workout session with id {id} updated successfully."}), 200

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get all workout sessions for a specific member
@app.route('/workout_sessions/<int:member_id>', methods=['GET'])
def get_workout_sessions_by_member(member_id):
    try:
        sessions = WorkoutSession.query.filter_by(member_id=member_id).all()
        if not sessions:
            return jsonify({"message": f"No workout sessions found for member with id {member_id}."}), 404
        return jsonify(workout_sessions_schema.dump(sessions)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get all workout sessions
@app.route('/workout_sessions', methods=['GET'])
def get_all_workout_sessions():
    try:
        sessions = WorkoutSession.query.all()
        return jsonify(workout_sessions_schema.dump(sessions)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500






















if __name__ == '__main__':
    app.run(debug=True)





