from pathlib import Path
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column,Integer, String, Text, Boolean,DateTime
#from .unit import logger
import datetime
import json
import re
Base = declarative_base()


class LocalBank(Base):
    # 表的名字:
    __tablename__ = 'banks'

    '''表的结构:
        id | category | content | options[item0, item1, item2, item3] | answer | note | bounds
        序号 | 题型 | 题干 | 选项 | 答案 | 注释 | 位置(保存时丢弃)
    '''
    id = Column(Integer,primary_key=True)
    createdAt=Column(DateTime)
    updatedAt=Column(DateTime)
    category = Column(String(128), default='radio') # radio check blank challenge
    content = Column(Text, default='content')
    item_a = Column(Text, default='item_a')
    item_b = Column(Text, default='')
    item_c = Column(Text, default='')
    item_d = Column(Text, default='')
    item_e = Column(Text, default='')
    item_f = Column(Text, default='')

    answer = Column(String(256), nullable=True, default='')
    excludes= Column(String(256), nullable=True, default='')
    notes = Column(Text, nullable=True, default='')

    @classmethod
    def from_dict(cls, data):
        options=['','','','','','']
        options[0]=data['item_a']
        options[1]=data['item_b']
        options[2]=data['item_c']
        options[3]=data['item_d']
        options[4]=data['item_e']
        options[5]=data['item_f']

        return cls(data['content'], data['category'], options, data['answer'], data['excludes'],data['notes'])

    def __init__(self,content,category,options,answer='',excludes='',notes=''):
        self.createdAt = datetime.datetime.now()
        self.updatedAt= datetime.datetime.now()
        self.code=''
        self.category=category or 'radio'
        self.content = content or 'default content'
        k=len(options)

        self.item_a='' if k<1 else options[0]
        self.item_b='' if k<2 else options[1]
        self.item_c='' if k<3 else options[2]
        self.item_d='' if k<4 else options[3]
        self.item_e='' if k<5 else options[4]
        self.item_f='' if k<6 else options[5]

        self.answer = answer.upper() or ''
        self.excludes=excludes.upper() or ''
        self.notes = notes or ''

class LocalModel():
    def __init__(self, database_uri):
        # 初始化数据库连接:
        engine = create_engine(database_uri)
        # 创建DBSession类型:
        Session = sessionmaker(bind=engine)

        Base.metadata.create_all(engine)
        self.session = Session()

    def query(self, content=None, item_a=None,category='挑战题 单选题 多选题 填空题'):
        '''数据库检索记录'''
        category = category.split(' ')
        #if id and isinstance(id, int):
        #    return self.session.query(Bank2).filter_by(id=id).one_or_none()
        if content and isinstance(content, str):
            #content = re.sub(r'\s+', '%', content)   #空格替换为%
            return self.session.query(LocalBank).filter(LocalBank.category.in_(category)).\
                filter(LocalBank.content.like(content)).filter(LocalBank.item_a.like(item_a)).one_or_none()
        return None    
        #return self.session.query(Bank2).filter(Bank2.category.in_(category)).all()

    def add(self, content,category,options):
        '''数据库添加纪录'''
        result = self.query(content=content, item_a=options[0],category=category)
        if result:
            pass #logger.info(f'数据库已存在此纪录，无需添加纪录！id:{result.id}')
        else:
            addbank=LocalBank(content,category,options)
            self.session.add(addbank)
            self.session.commit()
            #logger.info(f'数据库添加记录成功！id:{addbank.id}')

    def update_bank(self,category,content,options,answer,excludes,notes):            
        '''数据库更新记录'''
        if len(options)>0:
            item_a=options[0]
        else:
            item_a=''
        to_update = self.query(content=content,category=category,item_a=item_a)
        if to_update is None:
            print('when update not found.')
            return
        to_update.updatedAt= datetime.datetime.now()
        to_update.answer=answer
        to_update.excludes=to_update.excludes+excludes
        to_update.notes=notes
        self.session.commit()
        #logger.info(f'数据库更新记录成功！id:{to_update.id}')
        return

    def _from_json(self, path, catagory='挑战题 单选题 多选题 填空题'):
        if path.exists():
            with open(path,'r',encoding='utf-8') as fp:
                res = json.load(fp)
            recd=res.get('RECORDS')    
            for r in recd:
                addbank = LocalBank.from_dict(r)
                #found=self.session.query(LocalBank).filter(LocalBank.category.in_(addbank.category)).filter(\
                #    LocalBank.content.like(addbank.content)).filter(LocalBank.item_a.like(addbank.item_a)).one_or_none()
                found=self.session.query(LocalBank).filter(LocalBank.category.like(addbank.category)).filter(\
                    LocalBank.content.like(addbank.content)).filter(LocalBank.item_a.like(addbank.item_a)).one_or_none()

                if found:
                    print(f'数据库已存在此纪录，无需添加纪录！id:{found.id}')
                    pass #logger.info(f'数据库已存在此纪录，无需添加纪录！id:{found.id}')
                else:     
                    self.session.add(addbank) 
                    self.session.commit()
                    print(f'数据库添加记录成功！id:{addbank.id}')
                    #logger.info(f'数据库添加记录成功！id:{addbank.id}')
                    
            #logger.info(f'JSON数据成功导入{path}')
            return True
        else:
            #logger.debug(f'JSON数据{path}不存在')
            print(path)
            return False


localmodel = LocalModel('sqlite:///./wf.sqlite')

if __name__ == "__main__":
    path = Path('usr_banks.json')
    localmodel._from_json(path)
