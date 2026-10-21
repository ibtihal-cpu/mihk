import re,sys
def strip_comments(s):
    # يحذف /* */ و // خارج النصوص
    out=[];i=0;n=len(s);instr=False;q=''
    while i<n:
        c=s[i]
        if instr:
            out.append(c)
            if c=='\\': out.append(s[i+1]); i+=2; continue
            if c==q: instr=False
            i+=1; continue
        if c in '"\'': instr=True;q=c;out.append(c);i+=1;continue
        if s.startswith('/*',i):
            j=s.index('*/',i+2); i=j+2; continue
        if s.startswith('//',i):
            j=s.find('\n',i); i=n if j<0 else j; continue
        out.append(c);i+=1
    return ''.join(out)
def norm(s):
    s=strip_comments(s)
    return [re.sub(r'\s+',' ',l).strip() for l in s.split('\n') if l.strip()]
if __name__=='__main__':
    a=norm(open(sys.argv[1]).read()); b=norm(open(sys.argv[2]).read())
    print('lines',len(a),len(b),'IDENTICAL' if a==b else 'DIFFERENT')
    if a!=b:
        import difflib
        for l in list(difflib.unified_diff(a,b,lineterm=''))[:20]: print(l)
