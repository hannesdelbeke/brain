The Asset management system in Unreal breaks all Assets into two types, 
- Primary Assets and 
- Secondary Assets. 

Primary Assets can be manipulated directly by the Asset Manager from their Primary Asset ID, which is obtained by calling the function GetPrimaryAssetId. In order to designate Assets made from a specific UObject class as Primary Assets, you can override the GetPrimaryAssetId function to return a valid FPrimaryAssetId structure. 

Secondary Assets are not handled directly by the Asset Manager, but instead are loaded automatically by the Engine in response to being referenced or used by Primary Assets. 

By default, ==only UWorld Assets (levels) are Primary, all other Assets are Secondary==. 

In order to make a Secondary Asset into a Primary Asset, the GetPrimaryAssetId function for its class must be overridden to return a valid FPrimaryAssetId structure. 

A Primary Asset ID has two parts, a unique Primary Asset Type that identifies a group of Assets, and the name of that specific Primary Asset, which defaults to the Asset's name as it appears in the Content Browser.

[official docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/asset-management-in-unreal-engine)

[[Unreal - primary asset id|primary asset id]]