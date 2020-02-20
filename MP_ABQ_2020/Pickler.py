import sys

#Ueberpruefen ob Python 2 oder 3
if sys.version_info[0] < 3:
  import cPickle as pickle
  
  def dump(data,path):
    f=open(path,"wb")
    pickle.dump(data,f,protocol=2)
    f.close()
  
  def load(path):
    f=open(path,"rb")
    data=pickle.load(f)
    f.close()
    return data
  
else:
  import pickle
  
  def dump(data,path):
    f=open(path,"wb")
    pickle.dump(data,f,protocol=2)
    f.close()
  
  #Wenn das Pickle-File von Python 2 stammt muss der Parameter encoding="bytes" gesetzt werden
  def load(path):
    f=open(path,"rb")
    try:
      data=pickle.load(f)
    except:
      #File Offset auf 0 setzen
      f.seek(0)
      data=pickle.load(f,encoding="latin1")
    
    f.close()
    return data