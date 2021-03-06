from app import db
from passlib.hash import pbkdf2_sha256 as sha256
from sqlalchemy import func

"""
I think all the names of the functions are self-explaining
but I'll try to write what it does
Future me you're welcome ;)
"""

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(120), nullable = False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        """
        Returns username, id, password (hash)
        of supplied user
        """
        return cls.query.filter_by(username = username).first()

    @staticmethod
    def generate_hash(password):
        """
        I don't know what to write here
        """
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        """
        And here too :(
        """
        return sha256.verify(password, hash)

class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key = True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        """
        blacklist supplied jti token (used on logout)
        """
        query = cls.query.filter_by(jti = jti).first()
        return bool(query)


class DnsModel(db.Model):
    __tablename__ = 'dns_tokens'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique = False, nullable = False)
    uuid = db.Column(db.String(120), unique = True, nullable = False)
    props = db.Column(db.String(2056), unique = False, nullable = False)
    name = db.Column(db.String(120), unique = False, nullable = False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_uuid(cls, uuid):
        """
        Used in dns_resources to check if uuid exists
        """
        return cls.query.filter_by(uuid = uuid).first()

    @classmethod
    def find_by_user(cls, username):
        """
        Returns list all tokens that belong to supplied username
        """
        def to_json(x):
            return {'uuid': x.uuid, 'name': x.name}
        return list(map(lambda x: to_json(x), cls.query.filter_by(username = username)))

    @classmethod
    def get_props(cls, uuid, username):
        """
        Get properties of token (what it should resolve to, stuff like that...)
        """
        def to_json(x):
            return {
                'props': x.props,
                'name': x.name
            }
        try:
            return list(map(lambda x: to_json(x), cls.query.filter_by(uuid = uuid, username = username)))[0]
        except:
            return False

class LogModel(db.Model):
    __tablename__ = 'dns_logs'

    id = db.Column(db.Integer, primary_key = True)
    uuid = db.Column(db.String(64), unique = False, nullable = False)
    resolved_to = db.Column(db.String(253), unique = False, nullable = False)
    domain = db.Column(db.String(253), unique = False, nullable = False)
    ip = db.Column(db.String(120), unique = False, nullable = False)
    port = db.Column(db.String(32), unique = False, nullable = False)
    created_date = db.Column(db.String(128), unique = False, nullable = False)

    @classmethod
    def statistics_count(cls, username):
        """
        Returns statistics for user :O
        """
        def get_count(q):
            """
            Used for counting rows because SQLAlchemys count is slow af
            """
            count_q = q.statement.with_only_columns([func.count()]).order_by(None)
            count = q.session.execute(count_q).scalar()
            return count
        uuids = [x['uuid'] for x in DnsModel.find_by_user(username)]
        req_count = 0

        for uuid in uuids:
            req_count += get_count(cls.query.filter_by(uuid = uuid))

        return {'request_count': req_count, 'created_bins': len(uuids)}


    @classmethod
    def uuid_logs(cls, uuid, username):
        """
        Returns list of All the logs of supplied uuid
        I have to implement pagination for this
        because nobody wants to wait for eternity for 83298392 entries served over web api
        """
        def to_json(x):
            return {
                'uuid': x.uuid,
                'resolved_to': x.resolved_to,
                'domain': x.domain,
                'origin_ip': x.ip,
                'port': x.port,
                'created_date': x.created_date
            }
        if uuid in [y['uuid'] for y in DnsModel.find_by_user(username)]:
            return list(map(lambda x: to_json(x), cls.query.filter_by(uuid = uuid, )))
        else:
            return []
    @classmethod
    def return_all(cls, username):
        """
        Returns *ALL* of tokens that belong to supplied user
        I'm probably not gonna use this function
        """
        def to_json(x):
            return {
                'uuid': x.uuid,
                'resolved_to': x.resolved_to,
                'domain': x.domain,
                'origin_ip': x.ip,
                'port': x.port,
                'created_date': x.created_date
            }
        uuids = [y['uuid'] for y in DnsModel.find_by_user(username)]
        uuid_list = []
        for uuid in uuids:
            uuid_list += list(map(lambda x: to_json(x), cls.query.filter_by(uuid = uuid)))

        return uuid_list
