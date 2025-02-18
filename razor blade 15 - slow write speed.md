used [[AS SSD Benchmark]]
- **4K Read/Write**: represent the performance with random small files. 
- **4K-64thrd Read/Write**: This measures the performance with multiple threads.


C drive [[LITEON CV6-8Q128]], slow write speed.

| 1Gb test  | read     | write   |
| --------- | -------- | ------- |
| seq       | 480 MBps | 33 MBps |
| 4K        | 16.8     | 34.5    |
| 4K-64thrd | 165      | 30.9    |
| acc time  | .68 ms   | .16 ms  |
| score     | 230      | 69      |
another 50mb test shows write speed 110mbps

in safe mode

| 1Gb test  | read     | write   |
| --------- | -------- | ------- |
| seq       | 517 MBps | 473 MBps |
| 4K        | 21     | 54    |
| 4K-64thrd |  194     | 31    |
| acc time  | .23 ms   |  .14 ms  |
| score     |  268     |    133   |


[[Samsung SSD 840 DXT09B0Q - 2014]]

| 1Gb test  | read     | write    |
| --------- | -------- | -------- |
| seq       | 426 MBps | 2.8 MBps |
| 4K        | 23       | 1.54     |
| 4K-64thrd |          |          |
| acc time  | ms       | ms       |
| score     |          |          |
write speed seems broken.
still broken in safe mode

vid on upgrade https://www.youtube.com/watch?v=rYpfUf2nHbM

---

## UPdate
replaced SSD, faster speeds now.
used AS-SSD to test write speeds