
```c#
internal class MyClass
{
	// 19 is order in menu, false is checkbox state
	[MenuItem("Assets/command", false, 19)]  
	private static void MyCustomCommand()  
	{  
		Debug.Log("hello");  
	}
}
```