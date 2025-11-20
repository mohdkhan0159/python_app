import requests, time
BASE='http://127.0.0.1:8000'

def reg(e,p):
    r=requests.post(BASE+'/users/register', json={'email':e,'password':p}); print('reg', r.status_code, r.text)

def login(e,p):
    r=requests.post(BASE+'/users/login', json={'email':e,'password':p}); print('login', r.status_code, r.text); return r.json().get('access_token') if r.ok else None

def courses(t=None):
    h={} 
    if t: h['Authorization']='Bearer '+t
    r=requests.get(BASE+'/courses/', headers=h); print('courses', r.status_code); return r

def pay(e,c,t=None):
    h={}
    if t: h['Authorization']='Bearer '+t
    r=requests.post(BASE+'/payments/simulate', params={'user_email':e,'course_id':c}, headers=h); print('pay', r.status_code, r.text)

if __name__=='__main__':
    em='tester@example.com'; pw='password123'
    reg(em,pw)
    t=login(em,pw)
    time.sleep(0.5)
    courses(t)
    pay(em,1,t)
    print('done')
