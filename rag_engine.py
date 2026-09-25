from pathlib import Path
import numpy as np
class SimpleRAG:
    def __init__(self, folder='medical_docs'):
        self.docs=[]
        for p in sorted(Path(folder).glob('*.txt')):
            text=p.read_text(encoding='utf-8')
            self.docs.append({'title':text.splitlines()[0].replace('Title: ','') ,'text':text,'source':str(p)})
        words=sorted({w.lower().strip('.,:;()') for d in self.docs for w in d['text'].split()})
        self.vocab=words; self.pos={w:i for i,w in enumerate(words)}; vecs=[]
        for d in self.docs:
            v=np.zeros(len(words))
            for w in d['text'].split():
                w=w.lower().strip('.,:;()')
                if w in self.pos: v[self.pos[w]]+=1
            n=np.linalg.norm(v); vecs.append(v/n if n else v)
        self.matrix=np.array(vecs)
    def retrieve(self,q,k=3):
        v=np.zeros(len(self.vocab))
        for w in q.split():
            w=w.lower().strip('.,:;()')
            if w in self.pos: v[self.pos[w]]+=1
        n=np.linalg.norm(v)
        if n: v/=n
        scores=self.matrix@v
        return [{**self.docs[i],'score':round(float(scores[i]),3)} for i in np.argsort(scores)[::-1][:k] if scores[i]>0]
    def answer(self,q):
        rs=self.retrieve(q)
        if not rs: return 'No relevant educational documents found.',[]
        text='\n\n'.join(f"[{r['title']}]\n{r['text']}" for r in rs)
        return text+'\n\nEducational information only; consult a qualified clinician.',rs
