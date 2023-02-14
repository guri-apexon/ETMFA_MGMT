import datetime

from etmfa.db import db_context
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Index, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import FLOAT,INTEGER,ARRAY
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
import hashlib

class PDProtocolMetadata(db_context.Model):
    __tablename__ = "pd_protocol_metadata"

    # intake fields
    isActive = db_context.Column(db_context.Boolean(), default=True)
    id = db_context.Column(db_context.String(100), primary_key=True)
    userId = db_context.Column(db_context.String(100),index=True)
    fileName = db_context.Column(db_context.String(100))
    documentFilePath = db_context.Column(db_context.String(500))
    protocol = db_context.Column(db_context.String(500))
    projectId = db_context.Column(db_context.String(500))
    sponsor = db_context.Column(db_context.String(200))
    indication = db_context.Column(db_context.String(500))
    moleculeDevice = db_context.Column(db_context.String(500))
    amendment = db_context.Column(db_context.String(500))
    versionNumber = db_context.Column(db_context.String(200))
    documentStatus = db_context.Column(db_context.String(100))
    draftVersion = db_context.Column(db_context.String(500))
    uploadDate = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    # processing fields
    isProcessing= db_context.Column(db_context.Boolean(), default=True)
    errorCode = db_context.Column(db_context.Integer())
    errorReason = db_context.Column(db_context.String(500))
    percentComplete = db_context.Column(db_context.String(100))
    status = db_context.Column(db_context.String(100))
    qcStatus = db_context.Column(db_context.String(100))
    runId = db_context.Column(db_context.Integer(), default=0)
    compareStatus = db_context.Column(db_context.String(100))
    iqvXmlPathProc = db_context.Column(db_context.String(1500))
    iqvXmlPathComp = db_context.Column(db_context.String(1500))
    
    # output fields
    protocolTitle = db_context.Column(db_context.VARCHAR(None))
    shortTitle = db_context.Column(db_context.String(1500))
    phase = db_context.Column(db_context.String(500))
    digitizedConfidenceInterval = db_context.Column(db_context.String(500))
    completenessOfDigitization = db_context.Column(db_context.String(100))
    approvalDate = db_context.Column(db_context.DateTime(timezone=True))

    # placeholders
    studyStatus = db_context.Column(db_context.String(500))
    sourceSystem = db_context.Column(db_context.String(500))
    environment = db_context.Column(db_context.String(200))
    nctId = db_context.Column(db_context.String(100))

    # Audit fields
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    userCreated = db_context.Column(db_context.String(200))
    userUpdated = db_context.Column(db_context.String(200))


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
    
    def from_post_request(request, _id):
    
        this = PDProtocolMetadata()
        this.id = _id
        this.isProcessing = True
        this.percentComplete = '0'

        if request['sourceFileName'] is not None:
            this.sourceFileName = safe_unicode(request['sourceFileName'])
        else:
            file = request['file']
            this.sourceFileName = safe_unicode(file.filename)

        return this


class PDProtocolMetaDataLevel(db_context.Model):
    __tablename__ = "pd_protocol_metadata_level"
    id = db_context.Column(String, primary_key=True, nullable=False)
    level1 = db_context.Column(String)
    level2 = db_context.Column(String)
    level3 = db_context.Column(String)
    level4 = db_context.Column(String)
    level5 = db_context.Column(String)
    level6 = db_context.Column(String)
    parent_id = db_context.Column(String, ForeignKey('pd_protocol_metadata.id', ondelete="CASCADE"))
    pd_meta_data = relationship("PDProtocolMetadata", back_populates="levels")


PDProtocolMetadata.levels = relationship(
    "PDProtocolMetaDataLevel", back_populates="pd_meta_data", cascade="all, delete-orphan", passive_deletes=True)


class PDProtocolMetaDataAttribute(db_context.Model):
    __tablename__ = "pd_protocol_metadata_attribute"
    id = Column(String, primary_key=True, nullable=False)
    attribute_name = Column(String)
    attribute_type = Column(String)
    attribute_value_int = Column(INTEGER)
    attribute_value_string = Column(String)
    attribute_value_date=Column(DateTime)
    attribute_value_boolean= Column(Boolean)
    attribute_value_array=Column(ARRAY(String))
    confidence=Column(String)
    note=Column(String)
    parent_id = Column(String, ForeignKey('pd_protocol_metadata_level.id', ondelete="CASCADE"))
    meta_levels = relationship(
        "PDProtocolMetaDataLevel", back_populates="attributes")


PDProtocolMetaDataLevel.attributes = relationship(
    "PDProtocolMetaDataAttribute", back_populates="meta_levels", cascade="all,delete-orphan", passive_deletes=True)


def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return str(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return str(ascii_text)



class NestedDict():
    def __init__(self, max_levels=6):
        self.data = {}
        self.max_levels = max_levels

    def add_level(self, level_data):
        curr_data = self.data
        nested_fields = []
        for idx in range(1, self.max_levels+1):
            attr_name = getattr(level_data, 'level'+str(idx))
            if attr_name == None:
                break
            curr_data[attr_name] = curr_data.get(attr_name, {})
            curr_data = curr_data[attr_name]
            nested_fields.append(attr_name)
        return curr_data, nested_fields

    def get_attribute_value(self, attr_data, prefix):
        for attr in attr_data.__table__.columns:
            name = attr.name
            if name == None:
                continue
            if str(name).startswith(prefix):
                attr_value = getattr(attr_data, attr.name)
                if attr_value:
                    return attr_value


@dataclass
class MetaStatusResponse():
    isAdded: Boolean
    isDuplicate: Boolean = False
    error: str = ''

@dataclass
class MetaDeleteResponse():
    isDeleted:Boolean
    error:str
    

SUMMARY_MAPPED_FIELDS = {'Protocol Name': 'fileName',
                         'Protocol Number': 'protocol',
                         'Protocol title': 'protocolTitle',
                         'Protocol Title Short': 'shortTitle',
                         'Is Amendment': '',
                         'Amendment Number': 'amendment',
                         'Trial Phase': 'phase',
                         'Sponsor': 'sponsor',
                         'Sponsor Address': '',
                         'Drug': '',
                         'Approval Date': 'approvalDate',
                         'Version Number': 'versionNumber',
                         'Version Date': '',
                         'Blinded': '',
                         'Compound Number': '',
                         'Control': '',
                         'Investigator': '',
                         'Study Id': '',
                         'Number of Subjects': '',
                         'Participant Age': '',
                         'Participant Sex': '',
                         'Trial Type randomized':'',
                         'Molecule Device': 'moleculeDevice',
                         'Document Status': 'documentStatus',
                         'Indication': 'indication',
                         'Draft Version': 'draftVersion'
                         }


class MetaDataTableHelper():
    def __init__(self, max_level=6):
        self.max_level = max_level
        self.valid_level_range = list(range(1, max_level+1))
        self.variable_type_map = {'integer':'attribute_value_int',
                            'string':'attribute_value_string',
                            'date':'attribute_value_date',
                            'boolean':'attribute_value_boolean',
                            'array':'attribute_value_array'
                            }
    def get_session(self):
        session = db_context.session()
        return session
        
    def get_variable_types(self):
        return list(self.variable_type_map.keys())

    def getMetaParam(self, id):
        """
        get metaparams for specific docid
        """
        nested_obj = NestedDict(self.max_level)
        data = self.get_session().query(PDProtocolMetadata).get(id)
        if data == None:
            return {}
        for lvl_data in data.levels:
            curr_nested_obj, field_list = nested_obj.add_level(lvl_data)
        return nested_obj.data
        
    def add_child_info(self, obj):
        """
        adds child info
        """
        if not isinstance(obj, dict):
            return
        obj['_childs']=[]
        for key, value in obj.items():
            if isinstance(value, dict):
                obj['_childs'].append(key)
            self.add_child_info(value)

    def get_data(self, id, field_name=None):
        """
        Get all metadata
        """
        nested_obj = NestedDict(self.max_level)
        nested_fields, _ = self._get_level(field_name)
        data = self.get_session().query(PDProtocolMetadata).get(id)
        if data == None:
            return {}
        for lvl_data in data.levels:
            curr_nested_obj, field_list = nested_obj.add_level(lvl_data)
            if set(nested_fields).difference(set(field_list)):
                continue
            attribute_info = []
            for attr in lvl_data.attributes:
                attr_value = nested_obj.get_attribute_value(
                    attr, 'attribute_value')
                attribute_info.append({'attr_name': attr.attribute_name, 'attr_type':attr.attribute_type,
                                       'attr_value': attr_value, 'confidence': attr.confidence, 'note': attr.note})
            curr_nested_obj['_meta_data'] = attribute_info

        curr_obj = nested_obj.data
        if not field_name:
            top_obj = {c.name: getattr(data, c.name) for c in data.__table__.columns}
            result_list = []
            for display_name, attr_name in SUMMARY_MAPPED_FIELDS.items():
                if not attr_name:
                    attr_name = display_name
                result_list.append({'display_name':display_name,
                                    'attr_name': attr_name,
                                    'attr_value': top_obj.get(attr_name,'')})
            curr_obj.update({'summary':{'_meta_data':result_list}})

        if not curr_obj:
            return curr_obj
        self.add_child_info(curr_obj)
        for field in nested_fields:
            curr_obj = curr_obj.get(field,{})
        return {nested_fields[-1]: curr_obj} if nested_fields else curr_obj

    def _get_level_id(self, id, start_field, lvl, end_field):
        return self._get_elements_hash([id, start_field, lvl, end_field])

    def add_data(self, data):
        """
        add data
        """
        status, duplicate, error = True, False, False
        session = db_context.session()
        try:
            pd = PDProtocolMetadata(**data)
            session.add(pd)
            session.commit()
        except IntegrityError as e:
            status = False
            error=str(e)
            if isinstance(e.orig, UniqueViolation):
                error = str("duplication error")
                duplicate = True

        return MetaStatusResponse(isAdded=status, isDuplicate=duplicate, error=error).__dict__

    def _get_level(self, field_name):
        if not field_name:
            return [], 0
        nested_fields = field_name.split('.')
        level = len(nested_fields)
        if level not in self.valid_level_range:
            raise Exception(
                f"requested level outside range max level is {self.valid_level_range[-1]}")
        return nested_fields, level

    def _get_elements_hash(self, elm_list):
        joined_elm = "_".join(map(str, elm_list)).encode()
        result = hashlib.sha256(joined_elm)
        return result.hexdigest()

    def _get_meta_data_attr(self, id, data, start_field, end_field, level):
        meta_field = self.variable_type_map[data['attributeType']]
        name, type, value = data['attributeName'], data['attributeType'], data['attributeValue']
        attr_id = self._get_elements_hash(
            [id, start_field, level, end_field, name])
        meta_data_attr = PDProtocolMetaDataAttribute(id = attr_id)
        setattr(meta_data_attr, meta_field, value)
        meta_data_attr.attribute_name = name
        meta_data_attr.attribute_type = type
        meta_data_attr.confidence=data.get('confidence', None)
        meta_data_attr.note=data.get('note', None)
        return meta_data_attr

    def add_field_data(self, id, field_name=None, data_list=[]):
        """
        Add metadata field attributes
        """
        status, duplicate, error = True, False, False
        if not field_name:
            if not self.check_field_exist(id, 'summary_extended'):
                self.add_field(id, 'summary_extended')
                
            field_name = 'summary_extended'
        nested_fields, level = self._get_level(field_name)
        try:
            start_field, end_field = nested_fields[0],nested_fields[-1]
            lvl_id = self._get_level_id(id, start_field, level, end_field)
            meta_data_level = self.get_session().query(
                PDProtocolMetaDataLevel).get(lvl_id)
            if not meta_data_level:
                error= str(f"Field {field_name} does not exist")
                data_list=[]
            for data in data_list:
                meta_data_attr = self._get_meta_data_attr(id, data, start_field, end_field, level)
                meta_data_level.attributes.append(meta_data_attr)
            self.get_session().commit()
        except IntegrityError as e:
            status = False
            if isinstance(e.orig, UniqueViolation):
                error = str("duplication error")
                duplicate = True
            else:
                error=str(e)
        return MetaStatusResponse(isAdded=status, isDuplicate=duplicate, error=error).__dict__

    def check_field_exist(self,id,field_name):
        """
        Checks for existing fields
        """
        nested_fields, level = self._get_level(field_name)
        start_field, end_field = nested_fields[0],nested_fields[-1]
        lvl_id = self._get_level_id(id, start_field, level, end_field)
        meta_data_level = self.get_session().query(
            PDProtocolMetaDataLevel).get(lvl_id)
        if meta_data_level:
            return True
        return False

    def delete_field(self, id, field_name=None):
        """
        Delete metadata field
        """
        nested_obj = NestedDict(self.max_level)
        is_deleted,error = True,''
        nested_fields, _ = self._get_level(field_name)
        try:
            data = self.get_session().query(PDProtocolMetadata).get(id)
            if data == None:
                return {}
            if not field_name:
                self.get_session().delete(data)
            else:
                for lvl_data in data.levels:
                    _, field_list = nested_obj.add_level(lvl_data)
                    if set(nested_fields).difference(set(field_list)):
                        continue
                    lvl_id = self._get_level_id(id,nested_fields[0], len(field_list), nested_fields[-1])
                    obj=self.get_session().query(PDProtocolMetaDataLevel).get(lvl_id)
                    self.get_session().delete(obj)
        except Exception as e:
            is_deleted=False
            error=str(e)
        self.get_session().commit()
        return MetaDeleteResponse(isDeleted = is_deleted, error = error).__dict__

    def add_update_attribute(self, id, field_name, data_list=[]):
        """
        Update attributes
        """
        status, duplicate, error = True, False, False
        nested_fields, level = self._get_level(field_name)
        start_field, end_field = nested_fields[0], nested_fields[-1]
        parent_id = self._get_elements_hash([id, start_field, level, end_field])
        for data in data_list:
            try:
                attr = self._get_meta_data_attr(id, data, start_field, end_field, level)  
                obj = self.get_session().query(PDProtocolMetaDataAttribute).get(attr.id)
                if not obj:
                    attr.parent_id = parent_id
                    self.get_session().add(attr)
                else:
                    obj.parent_id = parent_id
                    for col in attr.__table__.columns:
                        col_name=col.name
                        if not col_name.startswith('attribute_value'):
                            continue
                        val = getattr(attr, col.name)
                        setattr(obj, col.name, val)
                self.get_session().commit()

            except IntegrityError as e:
                    status = False
                    error = str(e)
                    if isinstance(e.orig, UniqueViolation):
                        error = str("duplication error")
                        duplicate = True
        return MetaStatusResponse(isAdded=status, isDuplicate=duplicate, error=error).__dict__
    
    def update_primary_attributes(self,_id,data_list=[]):
        """
        Update parent attributes
        """
        status, duplicate, error = True, False, False
        try:
            for data in data_list:
                obj = self.get_session().query(PDProtocolMetadata).filter(PDProtocolMetadata.id == _id ).first()
              
                for col in PDProtocolMetadata.__table__.columns:
                        col_name=col.name
                        if col_name.startswith(data['attributeName']):
                            setattr(obj, col_name, data['attributeValue'])
                self.get_session().commit()
        except IntegrityError as e:
                status = False
                error = str(e)
                if isinstance(e.orig, UniqueViolation):
                    error = str("duplication error")
                    duplicate = True
        return MetaStatusResponse(isAdded=status, isDuplicate=duplicate, error=error).__dict__



    def delete_attribute(self, id, field_name, data_list=[]):
        """
        Delete metadata attribute
        """
        is_deleted, error = True,''
        nested_fields, level = self._get_level(field_name)
        start_field, end_field = nested_fields[0], nested_fields[-1]
        for data in data_list:
            name = data['attributeName']
            attr_id = self._get_elements_hash([id, start_field, level, end_field, name])
            try:
                obj=self.get_session().query(PDProtocolMetaDataAttribute).get(attr_id)
                if obj:
                    self.get_session().delete(obj)
                    self.get_session().commit()
            except Exception as e:
                status = False
                error=str(e)
        return MetaDeleteResponse(isDeleted = is_deleted, error=error).__dict__       
       
    
    def add_field(self, id, field_name):
        """
        Add metadata field
        """
        status, duplicate, error = True, False, False
        nested_fields, level = self._get_level(field_name)
        try:
            pd = self.get_session().query(PDProtocolMetadata).get(id)
            start_field, end_field = nested_fields[0], nested_fields[-1]
            lvl_id = self._get_level_id(id, start_field, level, end_field)
            l1 = PDProtocolMetaDataLevel(id=lvl_id)
            for idx, field in enumerate(nested_fields):
                setattr(l1, 'level'+str(idx+1), field)
            pd.levels.append(l1)
            self.get_session().commit()
        except IntegrityError as e:
            status = False
            error = str(e)
            if isinstance(e.orig, UniqueViolation):
                error = str("duplication error")
                duplicate = True
        return MetaStatusResponse(isAdded=status, isDuplicate=duplicate, error=error).__dict__