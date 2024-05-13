---
alias: unreal ProgressBar
---

Create an [[Unreal]] loading bar with pure [[Python]] code
![preview progressbar](https://img-blog.csdnimg.cn/20200229221939797.png)
```python
task_iter = # a custom function that returns steps, if no iter use range
with unreal.ScopedSlowTask(nr_of_steps, "DESCRIPTION") as slow_task:  
    slow_task.make_dialog(True)  
    for x in task_iter():  
        if slow_task.should_cancel():  
            break  
        slow_task.enter_progress_frame(1, f"loaded {x}/{nr_of_steps}")  
```

### references
- [[Unreal]] [ProgressBar docs](https://docs.unrealengine.com/5.0/en-US/PythonAPI/class/ProgressBar.html) 
- [source](https://blog.csdn.net/Jingsongmaru/article/details/104583654) code