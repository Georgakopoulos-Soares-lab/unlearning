"""Inert field extraction; distinguish index geometry from storage byte offsets."""
import pickletools
def storage_records(raw):
    memo={};nextmemo=0;atom=None;started=False;field=None;record={};records=[];fqn=None
    for op,arg,pos in pickletools.genops(raw):
        name=op.name
        if name in ['SHORT_BINUNICODE','BINUNICODE','UNICODE','BINUNICODE8']:atom=arg
        elif name in ['BININT','BININT1','BININT2','INT','LONG','LONG1','LONG4']:atom=arg
        elif name in ['BINGET','LONG_BINGET','GET']:atom=memo.get(int(arg))
        elif name=='MEMOIZE':memo[nextmemo]=atom;nextmemo+=1;continue
        elif name in ['BINPUT','LONG_BINPUT','PUT']:memo[int(arg)]=atom;nextmemo=max(nextmemo,int(arg)+1);continue
        elif name in ['PROTO','FRAME']:continue
        else:atom=None;continue
        if atom=='storage_data':started=True;continue
        if not started:continue
        if field:
            if field=='fqn':
                assert isinstance(atom,str);fqn=atom
            elif field in ['offset','length']:
                assert type(atom) is int;record[field]=atom
            else:
                assert isinstance(atom,str) and fqn is not None
                assert not record;record={'fqn':fqn,'relative_path':atom}
            field=None
            if 'length' in record:
                assert set(record)=={'fqn','relative_path','offset','length'}
                records.append(record);record={}
            continue
        if atom=='fqn':field='fqn'
        elif atom=='relative_path':field='relative_path'
        elif record and atom in ['offset','length']:field=atom
    assert records and not record and not field
    return records
