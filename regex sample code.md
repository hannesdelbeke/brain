```python
st = "yoyoyoyyo"  
f"test {st}"  
# 'test yoyoyoyyo'  
  
  
# regex example  
import re  
  
test = "call me 444-444-1001 yoyoyoy"  
phoneRegex = re.compile(r'\d\d\d\-\d\d\d\-\d\d\d\d')  
phoneRegex.search(test)  
# <re.Match object; span=(8, 20), match='444-444-1001'>  
matchObject = phoneRegex.search(test)  
print(matchObject.group)  
# <built-in method group of re.Match object at 0x0000011D57C34650>  
print(matchObject.group())  
# 444-444-1001  
phoneRegex = re.compile(r'(\d\d\d)\-(\d\d\d\-\d\d\d\d)')  
matchObject = phoneRegex.search(test)  
print(matchObject.group(1))  
# 444  
print(matchObject.group(2))  
# 444-1001  
  
  
#pipes  
# | the pipe char can match one of many possible groups  
batRegex = re.compile(r'Bat(man|mobile|copter|bat)')  
mo = batRegex.search('Batmobile lost wheel');  
mo.group();  
# 'Batmobile  
mo = batRegex.search('Batmobile lost wheel');  
mo  
#None  
  
batRegex = re.compile(r'Bat(wo)?man')  
mo.group()  
# 'Batman'  
  
mo = batRegex.search('The adventures of Batwoman')  
mo.group()  
# batwoman  
  
haRegex = re.compile(r'(Ha){3}')  
haRegex.search('He said "HaHaHa"')  
  
digitRegex = re.compile(r'(\d){3,5}')  
digitRegex.search('1234567890')  
# greedy match mathes max amount 5 : 12345  
digitRegex = re.compile(r'(\d){3,5}?')  #note hte question mark  
digitRegex.search('1234567890')  
# non-greedy match matches min amount 3 : 123  
  
# ? 0 or 1  
# + 1 or more  
# * 0 or more  
# {x} x times  
# {x,y} at least x , at most y times
```

[[Python stubs]]
