from gen import *
T=lambda t,d,**k: dict(k='text',t=t,d=d,**k)
V={}
V['t1_paid_to_be_lied']=[
 T("POV:\nyou paid *$3.99*\nto be lied to",1.3,size=100),
 T("and it\n*WORKED.*",0.9,size=130,bg=RED),
 T("the book is called",0.8,size=80),
 T("NOW\nONLY\n*LIES*",1.1,size=170),
 dict(k='alert',d=1.9),
 T("so you can't\neven complain",1.0,size=96),
 T("you're\n*stuck.*",1.0,size=150,bg=RED),
 T("link in caption",0.9,size=80,bg=WH),
 T("POV:\nyou paid *$3.99*\nto be lied to",0.7,size=100)]
V['t2_dont_google']=[
 dict(k='search',q='what is NOL',d=3.0),
 T("everyone who\ngoogled it:",1.0,size=96),
 T("bought\nthe book.",1.1,size=130,bg=RED),
 T("(it's $3.99)\n(it's *15 pages*)\n(2 look broken)",1.6,size=84),
 T("*don't*\ngoogle NOL.",1.2,size=120),
 dict(k='search',q='what is NOL',d=0.6)]
V['t3_billionaire_rules']=[
 T("3 \"billionaire rules\"\nfrom a book\nthat *only lies*",1.6,size=82),
 T("RULE 1\n*sell a dream.*\nnot a product.",1.3,size=96),
 T("RULE 2\n*your face*\nis optional.",1.3,size=104),
 T("RULE 3\nmake it *cheaper*\nthan a bad decision.",1.4,size=88),
 T("i'm not\na billionaire\neither.",1.1,size=100,bg=WH),
 T("*not yet.*",1.0,size=160,bg=RED),
 T("3 \"billionaire rules\"\nfrom a book\nthat *only lies*",0.6,size=82)]
V['t4_page8']=[
 T("page 8\n*broke me.*",1.2,size=140),
 dict(k='page7',d=1.3),
 dict(k='glitch',d=1.5,top='PAGE 8',t='*...what?*',size=90),
 T("no.\nkeep\n*scrolling.*",1.2,size=140,bg=RED),
 T("it's a $3.99 PDF.\nthe title\ntells you it lies.",1.6,size=84),
 T("page 8\n*broke me.*",0.7,size=140)]
V['t5_scam_logic']=[
 T("is it a\n*scam?*",1.1,size=150),
 T("the title says:\nNOW ONLY *LIES*",1.3,size=92),
 T("so if you say\n\"it's a scam\"",1.1,size=96),
 T("that's a\n*lie.*",1.0,size=170,bg=RED),
 T("so it's\nnot a scam.",1.1,size=120),
 T("so you\nare *stuck.*",1.1,size=130),
 T("Fall in\n*NOL.*",1.4,size=170,bg=WH),
 T("is it a\n*scam?*",0.6,size=150)]
import sys
only=sys.argv[1:] 
for k,b in V.items():
    if only and k not in only: continue
    render(b,f'{k}.mp4'); print(k,sum(x['d'] for x in b))
