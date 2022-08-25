from flask import Flask
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.middleware.proxy_fix import ProxyFix
import os

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

db_host = os.environ['DB_HOST']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_port = os.environ['DB_PORT']
db_name = os.environ['DB_NAME']

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"db2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name};SECURITY=SSL;PROTOCOL=TCPIP;"

db = SQLAlchemy(app)
api = Api(
    app,
    version="1.0",
    title="Ticket API",
    description="A simple Ticket API to communicate with Watson Assistant chatbot "
    "via custom extension (build on Open API 3 documentation)",

)

ns = api.namespace("tickets", description="Tickets operations")
ticket_base = api.model(
    "TicketBase",
    {
        "TITLE": fields.String(required=True),
        "DESCRIPTION": fields.String(required=True),
    },
)

ticket = api.clone(
    "Ticket",
    ticket_base,
    {
        "PK": fields.Integer(required=True),
        "RESOLUTION_TEXT": fields.String(required=True),
        "CREATED_ON": fields.DateTime(required=True),
        "LAST_UPDATE_ON": fields.DateTime(required=True),
        "CLOSED_ON": fields.DateTime(required=True),
        "STATUS": fields.String(required=True),
        "PRIORITY": fields.String(required=True),
    },
)

ticket_priority = api.model(
    "Ticket",
    {
        "PRIORITY": fields.String(required=True),
    },
)

ticket_status = api.model(
    "Ticket",
    {
        "STATUS": fields.String(required=True),
    },
)


@app.after_request
def return_resp(resp):
    db.session.commit()
    return resp


class TicketModel(db.Model):
    __tablename__ = "TICKETS"
    PK = db.Column(db.Integer, primary_key=True)
    TITLE = db.Column(db.String(100), nullable=False)
    DESCRIPTION = db.Column(db.String(1000), nullable=False)
    RESOLUTION_TEXT = db.Column(db.String(1000), nullable=True)
    CREATED_ON = db.Column(db.DateTime, server_default=func.now())
    LAST_UPDATE_ON = db.Column(db.DateTime, onupdate=func.now())
    CLOSED_ON = db.Column(db.DateTime, nullable=True)
    STATUS = db.Column(db.String(20), default="new")
    PRIORITY = db.Column(db.String(20), default="low")


class TicketManager(object):
    @staticmethod
    def get(pk):
        ticket = TicketModel.query.filter_by(PK=pk).first()
        if ticket:
            return ticket
        api.abort(404, f"Ticket with pk: {pk} doesn't exist")

    @staticmethod
    def get_all():
        tickets = TicketModel.query.all()
        return tickets

    @staticmethod
    def create(data):
        new_ticket = TicketModel(**data)
        db.session.add(new_ticket)
        db.session.flush()
        return new_ticket

    @staticmethod
    def update(pk, data):
        updated_ticket = {}
        if data.get("PRIORITY"):
            updated_ticket = TicketModel.query.filter_by(PK=pk).update(
                {"PRIORITY": data["PRIORITY"]}
            )
        elif data.get("STATUS"):
            updated_ticket = TicketModel.query.filter_by(PK=pk).update(
                {"STATUS": data["STATUS"]}
            )
        return updated_ticket

    @staticmethod
    def delete(pk):
        TicketModel.query.filter_by(PK=pk).delete()


@ns.route("/ticket/create/")
class TicketCreate(Resource):
    @ns.doc("create_ticket")
    @ns.expect(ticket_base)
    @ns.marshal_with(ticket_base, code=201)
    def post(self):
        return TicketManager.create(api.payload), 201


@ns.route("/ticket/<int:pk>/")
@ns.response(404, "Ticket not found")
@ns.param("pk", "The ticket unique identifier")
class TicketGet(Resource):
    @ns.doc("get_ticket")
    @ns.marshal_list_with(ticket)
    def get(self, pk):
        return TicketManager.get(pk)


@ns.route("/ticket/all/")
class TicketGetAll(Resource):
    @ns.doc("list_tickets")
    @ns.marshal_list_with(ticket)
    def get(self):
        return TicketManager.get_all()


@ns.route("/ticket/update/priority/<int:pk>/")
@ns.response(404, "Ticket not found")
@ns.param("pk", "The ticket unique identifier")
class TicketUpdatePriority(Resource):
    @ns.doc("update_ticket_priority")
    @ns.expect(ticket_priority)
    @ns.response(204, "Ticket updated")
    def put(self, pk):
        return TicketManager.update(pk, api.payload)


@ns.route("/ticket/update/status/<int:pk>/")
@ns.response(404, "Ticket not found")
@ns.param("pk", "The ticket unique identifier")
class TicketUpdateStatus(Resource):
    @ns.doc("update_ticket_status")
    @ns.expect(ticket_status)
    @ns.response(204, "Ticket updated")
    def put(self, pk):
        return TicketManager.update(pk, api.payload)


@ns.route("/ticket/delete/<int:pk>/")
@ns.response(404, "Ticket not found")
@ns.param("pk", "The ticket unique identifier")
class TicketDelete(Resource):
    @ns.doc("delete_ticket")
    @ns.response(204, "Ticket deleted")
    def delete(self, pk):
        TicketManager.delete(pk)
        return "", 204


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
    # app.run(debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)
