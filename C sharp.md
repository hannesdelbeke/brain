---
aliases:
- C#
sentiment:
- 5
sentiment-hash: 5e0e2216
sentiment-label:
- factual
tags:
- technical
- work
- hobby
---

## `C#`
compiles source code to [[Common intermediate Language|CIL]] during **compile time**
the C Sharp Compiler `csc.exe` lives in the [[dot NET|.NET]] Framework install folder.
CIL can be found in the .exe and .dll binaries. [[assembly]]
each machine gets the same assembly (.exe file).
but machines and CPUs are different, so on execution the [[Common Language Runtime|CLR]] translates the CIL to instructions for the machine it runs on. This execution is called **runtime**.

```mermaid
flowchart LR
    subgraph src["Source Code"]
        b1["C# Code"]
    end

    subgraph byte["Byte Code"]
        b2["CIL Code"]
    end

    subgraph machine["Machine Code"]
        b3["Native Code"]
    end

    b1 -->|"C# Compiler"| b2 -->|"CLR"| b3
    c1["Design Time"] --> c2["Compile Time"] --> c3["Runtime"]
```

#### terms
source code
byte code 
c# code
c# compiler 
CIL code
compile time
CLR
machine code
native code 
runtime

[[programming language]]
