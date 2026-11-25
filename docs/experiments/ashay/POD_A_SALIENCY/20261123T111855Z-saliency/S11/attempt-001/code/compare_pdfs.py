from pathlib import Path
import sys,json,hashlib
import pymupdf
original=Path(sys.argv[1]);recreated=Path(sys.argv[2]);dest=Path(sys.argv[3]);checks=[]
for name,expected_pages in [('REVIEWER_SUMMARY',4),('RESULTS',12)]:
 a=original/(name+'.pdf');b=recreated/(name+'.pdf');da=pymupdf.open(a);db=pymupdf.open(b);assert len(da)==len(db)==expected_pages;pages=[]
 for i,(pa,pb) in enumerate(zip(da,db)):
  assert pa.rect==pb.rect and pa.get_text()==pb.get_text();xa=pa.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False);xb=pb.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False);ha=hashlib.sha256(xa.samples).hexdigest();hb=hashlib.sha256(xb.samples).hexdigest();assert ha==hb,(name,i,'PAGE_RENDER_CHANGED');pages.append({'page':i+1,'dimensions':[xa.width,xa.height],'RGB_pixel_sha256':ha,'text_equal':True})
 checks.append({'document':name,'pages':len(da),'original_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'recreated_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'byte_equal':a.read_bytes()==b.read_bytes(),'all_page_text_and_RGB_render_equal':True,'page_checks':pages})
dest.write_text(json.dumps({'status':'PASS','PDFs':checks,'equivalence_policy':'Exact final committed producer PDF bytes verified separately; fresh compiler outputs checked for raw equality, exact extracted text and every page RGB pixels at108dpi. Any raw metadata inequality explicitly recorded, never misreported as byte equality.'},indent=2)+'\n');print('PDF_RECONSTRUCTION_PASS',[(r['document'],r['byte_equal']) for r in checks],flush=True)
