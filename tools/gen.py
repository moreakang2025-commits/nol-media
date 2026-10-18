import sys, subprocess, random, numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H,FPS=720,1280,24
SANS='/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
MONO='/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf'
MONOR='/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'
RED=(235,26,41); CY=(0,217,230); WH=(245,245,245); GR=(130,130,130); BK=(8,8,8); YL=(255,222,23)
F=lambda p,s: ImageFont.truetype(p,int(s))
rng=np.random.default_rng(3)
NOISE=rng.normal(0,7,(H+60,W+60,1))

def bgimg(col,t):
    ox,oy=int(rng.integers(0,60)),int(rng.integers(0,60))
    n=NOISE[oy:oy+H,ox:ox+W]
    a=(np.array(col,dtype=float)[None,None,:]+n).clip(0,255)
    return a.astype('uint8')

def parse(line):
    toks=[];red=False
    for part in line.split('*'):
        for w in part.split(' '):
            if w: toks.append((w,red))
        red=not red
    return toks

def draw_block(img,text,size,col=WH,acc=RED,t=0.0,y0=None,font=SANS,punch=True):
    s=1.22*(1+(0.16*max(0,1-t/0.22) if punch else 0))
    fs=size*s
    f=F(font,fs); d=ImageDraw.Draw(img)
    maxw=W-90
    lines=[]
    for raw in text.split('\n'):
        toks=parse(raw); cur=[];cw=0
        for w,r in toks:
            ww=d.textlength(w+' ',font=f)
            if cur and cw+ww>maxw: lines.append(cur);cur=[];cw=0
            cur.append((w,r,ww));cw+=ww
        lines.append(cur)
    lh=fs*1.12; total=lh*len(lines)
    y=(H-total)/2 if y0 is None else y0
    for ln in lines:
        lw=sum(x[2] for x in ln)-d.textlength(' ',font=f)
        x=(W-lw)/2
        for w,r,ww in ln:
            c=acc if r else col
            for dx,dy,cc in((-3,0,CY),(3,1,RED)):
                if col!=RED and not r: d.text((x+dx,y+dy),w,font=f,fill=cc)
            d.text((x,y),w,font=f,fill=c)
            x+=ww
        y+=lh

def glitch(a,strength):
    a=a.copy(); y=0
    while y<H:
        h=int(rng.integers(8,70)); 
        if rng.random()<strength:
            s=int(rng.integers(-90,90)); a[y:y+h]=np.roll(a[y:y+h],s,axis=1)
            if rng.random()<0.5:
                a[y:y+h,:,0]=np.roll(a[y:y+h,:,0],int(rng.integers(8,30)),axis=1)
        y+=h
    return a

def chrome_title(img,label):
    d=ImageDraw.Draw(img); d.rectangle((60,H//2-210,W-60,H//2+210),fill=(26,26,26),outline=WH,width=3)
    d.rectangle((60,H//2-210,W-60,H//2-160),fill=RED); d.text((80,H//2-185),label,font=F(MONO,26),fill=BK,anchor='lm')
    d.text((W-80,H//2-185),'X',font=F(MONO,26),fill=BK,anchor='rm')

def beat_frame(b,t,bt):
    kind=b['k']
    bg=b.get('bg',BK)
    a=bgimg(bg,t)
    img=Image.fromarray(a)
    gl=0
    if kind=='text':
        col=b.get('col',BK if bg in(WH,YL,RED) and bg!=RED else WH)
        if bg==RED: col=BK
        if bg in (WH,YL): col=BK
        draw_block(img,b['t'],b.get('size',92),col=col,acc=(RED if bg not in(RED,) else WH),t=t)
        gl=0.25 if t<0.2 else 0.04
    elif kind=='alert':
        chrome_title(img,'SYSTEM NOTICE'); d=ImageDraw.Draw(img)
        d.text((W//2,H//2-60),'"this is a scam"',font=F(MONO,44),fill=WH,anchor='mm')
        if t>0.5: d.text((W//2,H//2+20),'= a lie.',font=F(MONO,70),fill=RED,anchor='mm')
        if t>1.0: d.text((W//2,H//2+95),'Reason: read the title.',font=F(MONOR,28),fill=GR,anchor='mm')
        for x in(W//2-130,W//2+130):
            d.rectangle((x-90,H//2+140,x+90,H//2+190),fill=WH); d.text((x,H//2+165),'OK',font=F(MONO,28),fill=BK,anchor='mm')
        gl=0.3 if t<0.2 else 0.05
    elif kind=='search':
        d=ImageDraw.Draw(img); q=b['q']
        n=min(len(q),int(t*12)); txt=q[:n]+('|' if int(t*3)%2==0 and n<len(q) else '')
        d.rounded_rectangle((40,300,W-40,390),radius=45,fill=(30,30,30),outline=GR,width=2)
        d.text((80,345),txt,font=F(MONOR,40),fill=WH,anchor='lm')
        if n>=len(q):
            d.text((60,450),'About 0 results (0.00 seconds)',font=F(MONOR,24),fill=GR)
            if t>(len(q)/12+0.5):
                d.text((60,520),'Did you mean:',font=F(MONOR,32),fill=WH)
                draw_block(img,"*don't.*",110,t=t-len(q)/12-0.5,y0=570)
        gl=0.05
    elif kind=='glitch':
        d=ImageDraw.Draw(img)
        y=330
        for i in range(10):
            h=int(rng.integers(14,46)); s=int(rng.integers(-120,160))
            c=[RED,CY,(60,60,60),WH,(30,30,30)][int(rng.integers(0,5))]
            d.rectangle((50+max(s,0),y,W-50+min(s,0),y+h),fill=c); y+=h+int(rng.integers(4,14))
        d.text((60,200),b.get('top','PAGE 8'),font=F(MONO,60),fill=RED)
        if b.get('t'): draw_block(img,b['t'],b.get('size',60),y0=1010,t=t)
        gl=0.5
    elif kind=='page7':
        d=ImageDraw.Draw(img)
        d.text((60,300),'PAGE 7',font=F(MONO,44),fill=GR)
        d.text((60,380),'"The secret is\non the next page."',font=F(MONOR,52),fill=WH)
        gl=0.02
    arr=np.array(img)
    if gl and rng.random()<0.9: arr=glitch(arr,gl*2)
    # corner tag
    return arr

def render(beats,out):
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-shortest','-c:v','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','32k','-movflags','+faststart',out],stdin=subprocess.PIPE)
    for b in beats:
        n=int(round(b['d']*FPS))
        for i in range(n):
            fr=beat_frame(b,i/FPS,b['d'])
            p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
