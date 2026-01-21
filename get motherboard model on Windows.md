identify [[motherboard]]
```powershell
Get-WmiObject Win32_BaseBoard | Format-List Product, Manufacturer
```

output
```
Product      : PRIME Z790-P WIFI D4
Manufacturer : ASUSTeK COMPUTER INC.
```