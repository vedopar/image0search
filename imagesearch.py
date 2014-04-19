#coding=utf-8
'''
Created on 2012-2-15

@author: vedopar
'''

numOfPages=10
import cookielib,urllib2,MultipartPostHandler,re,sqlite3,math,subprocess

def clean_stop_words(sentence):
    stopset={'\xa3\xbf','\xa3\xba','\xa1\xb0','\xa1\xb1',' ','-','(',')',',','\t','.','<','>','_','\\','\'','\"','\n','!','~','?','[',']',';',':'}
    for i in stopset:
            sentence=sentence.replace(i,"")
    return sentence

def baidu_search(info,db):
    c=db.cursor()
    c.execute('drop table if exists baidu_search;')
    c.execute('create table baidu_search(id integer primary key,title text,descr text);')
    imageCount=[0]
    cookies =cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
    params={
            "image":    open(info["addr"]+info["image"],'rb')
            }
    p=opener.open("http://stu.baidu.com/i?rt=0&pn=0&rn=10&ct=0&tn=baiduimagepc", params)
    baidu_parse(p,imageCount,c)
    if imageCount[0] == 10:
        url=p.geturl().replace('pn=0','pn=10').replace('rn=10','rn=20')
        p=urllib2.urlopen(url)
        baidu_parse(p,imageCount,c)
    print "done. Baidu_search count:"+str(imageCount[0])
    c.close()
    opener.close()
    return select_match(0,db)
    
    
def baidu_parse(p,count,c):
    pr=p.read().replace('\r','').replace('\n','').replace('\t',' ')
    rex=re.compile('fromPageTitleEnc:"(.*?)", textHost:"(.*?)"')
    for i in rex.finditer(pr):
        count[0]=count[0]+1
        c.execute('insert into baidu_search values(NULL,?,NULL)',(unicode(clean_stop_words(i.group(1).decode('gbk').encode('utf-8'))),))


def sogou_search(info,db):
    c=db.cursor()
    c.execute('drop table if exists sogou_search;')
    c.execute('create table sogou_search(id integer primary key,title text,descr text);')
    imageCount=[0]
    cookies =cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),
                                MultipartPostHandler.MultipartPostHandler)
    params={
            "pic_path":    open(info["addr"]+info["image"],'rb')
            }
    p=opener.open("http://pic.sogou.com/ris_upload", params)
    sogou_parse(p,imageCount,c)
    if imageCount[0] == 7:
        url=p.geturl()+"len=10&start="
        for i in range(2):
            urlTemp=url+str(i)+'7'
            p=urllib2.urlopen(urlTemp)
            sogou_parse(p,imageCount,c)
            if imageCount[0] < i*10+17:break
    print "done. Sogou_search count:"+str(imageCount[0])
    c.close()
    opener.close()
    return select_match(1,db)
    
    
def sogou_parse(p,count,c):
    p1=p.read().replace('\r','').replace('\n','').replace('\t',' ')
    rex=re.compile('uigs="result_link" target="_blank" href=.*?>(.*?)</a> </h3>.*?<div>(.*?)</div>')
    for i in rex.finditer(p1):
        count[0]=count[0]+1
        #descrTemp=clean_stop_words(re.sub('</?[^>]+>','',i.group(2)).replace('&gt;',''))
        c.execute('insert into sogou_search values(NULL,?,NULL)',(unicode(clean_stop_words(re.sub('</?[^>]+>','',i.group(2).decode('gbk','ignore').encode('utf-8','ignore')))),))

    
def google_search(info,db):
    c=db.cursor()
    c.execute('drop table if exists google_search;')
    c.execute('create table google_search(id integer primary key,title text,descr text);')
    imageCount=[0]
    data = {
    'image_url': "",
    'image_content': "",
    'filename': "",
    'encoded_image': open(info["addr"]+info["image"],"rb"),
    'num': "20",
    'hl': 'zh-CN',
    'newwindow': "1",
    'safe': 'strict',
    'bih': '417',
    'biw': '1272',
    }
    
    headers = [
    ("Host", "www.google.com.hk"),
    ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:6.0.2) Gecko/20100101 Firefox/6.0.2"),
    ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    ("Accept-Language", "en-us,en;q=0.5"),
    ("X-Content-Type-Options", "nosniff"),
    ("Server", "quimby_frontend"),
    ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7"),
    ("Connection","keep-alive"),
    ("Referer", "http://www.google.com.hk/imghp"),
    ]
    
    url='http://www.google.com.hk/searchbyimage/upload'
    cookies = cookielib.CookieJar()
    cookies.clear_session_cookies()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies),MultipartPostHandler.MultipartPostHandler())
    opener.addheaders=headers
    for i in range(3):
        data['start']=str(20*i)
        p=opener.open(url,data=data)
        google_parse(p,imageCount,c)
        #if imageCount[0] < i*20+5:break
    
    opener.close()
    c.close()
    return select_match(2,db)
    print "done. count:"+str(imageCount[0])
    

def google_parse(p,count,c):
    p1=p.read().replace('\r','').replace('\n','').replace('\t',' ')
    rex=re.compile('<table class=ts>[\s\S]{0,240}?imgurl=(.*?)&amp;.*?imgrefurl=(.*?)&amp;.*?<h3 class="r"><a .*?href=(.*?)>(.*?)</a>.*?')    
    for m in rex.finditer(p1):
        count[0]=count[0]+1
        title=(clean_stop_words(re.sub('</?[^>]+>','',m.group(4)))).decode('utf-8','ignore')
        c.execute('insert into google_search values(NULL,?,"")',(unicode(title),))
    
def similarity(v1,v2):
    product=0
    square1=0
    square2=0
    for i in range(len(v2)):
        product=product+v1[i]*v2[i]
        square1=square1+v1[i]*v1[i]
        square2=square2+v2[i]*v2[i]
    div=math.sqrt(square1)*math.sqrt(square2)
    if div == 0:
        return 0
    else:
        return product/div

def select_match(choice,db):
    c=db.cursor()
    print 'begin'
    wordset=set()
    search=''
    if choice == 0:
        search='baidu_search'
    elif choice == 1:
        search='sogou_search'
    elif choice == 2:
        search='google_search'
        
    c.execute('select title from '+search+';')
    countLine=0
    for i in c.fetchall():
        countLine=countLine+1
        for j in i[0]:
            wordset.add(j)
    wordset=set(wordset)
    word_count=len(wordset)
    tf_idf_matrix=[[0 for i in range(word_count)] for i in range(countLine)]
    doc_count=[0 for i in range(word_count)]
    m_x=0
    m_y=0
    c.execute('select title from '+search+';')
    for ti in c.fetchall():
        for kw in wordset:
            if kw in ti[0]:
                tf_idf_matrix[m_y][m_x]=1+math.log10(1+math.log10(ti[0].count(kw)))
                #tf_idf_matrix[m_y][m_x]=ti[0].count(kw)/len(ti[0])
                doc_count[m_x]=doc_count[m_x]+1            
            else:
                tf_idf_matrix[m_y][m_x]=0
            m_x=m_x+1
        m_x=0
        m_y=m_y+1
    idf_constant=math.log10(1+countLine)
    for x in range(word_count):
        for y in range(countLine):
            tf_idf_matrix[y][x]=(idf_constant-math.log10(doc_count[x]))*tf_idf_matrix[y][x]
            #tf_idf_matrix[y][x]=idf_constant*tf_idf_matrix[y][x]
            
    sim_matrix=[[0 for i in range(countLine)] for i in range(countLine)]
    m_x=0
    m_y=0
    for row in range(countLine):
        for column in range(row+1):
            sim_matrix[column][row]=similarity(tf_idf_matrix[row],tf_idf_matrix[column])
            sim_matrix[row][column]=sim_matrix[column][row]
    
    is_sorted=[-1 for i in range(countLine)]
    after_sorting=[]
    sort_num=[]
    
    #to cluster data into groups
    for row in range(countLine):
        for column in range(row):
            if sim_matrix[row][column] >= 0.5:
                if is_sorted[row] !=-1 and  is_sorted[column] != -1:
                    continue
                elif is_sorted[row] != -1:
                    is_sorted[column]=is_sorted[row]
                    after_sorting[is_sorted[column]].append(column)
                    sort_num[is_sorted[row]]=sort_num[is_sorted[row]]+1
                elif is_sorted[column] != -1:
                    is_sorted[row]=is_sorted[column]
                    after_sorting[is_sorted[row]].append(row)
                    sort_num[is_sorted[column]]=sort_num[is_sorted[column]]+1
                else:
                    is_sorted[column]=len(sort_num)
                    is_sorted[row]=len(sort_num)
                    after_sorting.insert(len(sort_num),[row,column])
                    sort_num.append(2)
    for row in range(countLine):
        if is_sorted[row] == -1:
            is_sorted[row]=len(sort_num)
            after_sorting.insert(len(sort_num),[row])
            sort_num.append(1)
    # the nlp course

    c.execute('drop table if exists nlp_result')
    c.execute('create table nlp_result(id integer primary key,beforenlp text,afternlp text);')
    selected_sentences=[]          
    if len(sort_num) >= 3:
        for i in range(3):
            selected_sentences.append(sort_num.index(max(sort_num)))
            c.execute('insert into nlp_result select null,title,null from '+search+' where id='+str(after_sorting[selected_sentences[-1]][0]+1))
            sort_num[selected_sentences[-1]]=0
    else:
        selected_sentences=[i for i in range(len(after_sorting))]
        for sort in after_sorting:
            c.execute('insert into nlp_result select null,title,null from '+search+' where id='+str(sort[0]+1))
    
    for i in selected_sentences:
        print i
    
    c.execute('select id,title from '+search)
    for i in c.fetchall():
        print i[0]-1,i[1].decode("utf-8","ignore")
               
    c.close()
    db.commit()
    db.close()
  
    pcs=subprocess.Popen("testdb.exe \n")
    while 0 != subprocess.Popen.poll(pcs):
        continue;
    
    db=sqlite3.connect("firstry")
    db.text_factory = str 
    c=db.cursor() 
    count=0
    
    c.execute('select id,beforenlp,afternlp from nlp_result')
    for i in c.fetchall():
        #print i[0]
        result_words=i[2].split(" ")
        result_words=[value for value in result_words if value != ""]
        root_id=0
        for i in range(len(result_words)):
            result_words[i]=result_words[i].split("/")
            if result_words[i][3] == '' or result_words[i][3] == '\n':
                root_id=i
        tempstring=''
        for i in result_words:
            if (i[2]==str(root_id) or result_words.index(i)==root_id) and i[0] != '\xb5\xc4':
                tempstring=tempstring+i[0].decode('gb2312','ignore').encode("utf-8",'ignore')
        print '\n'
        print tempstring
        print after_sorting[selected_sentences[count]]
        print '\n'
        count=count+1
    c.close()
    db.commit()
    db.close()
    
if __name__ == '__main__':
    db=sqlite3.connect('firstry')
    image='2.jpg'
    #image='test.jpg'
    #image="tom.jpg"
    info={"addr":"C:/Users/vedopar/Desktop/tuku/",
          "image":image}
    baidu_search(info,db)
    #sogou_search(info,db)
    #google_search(info,db)

    
    
    

    