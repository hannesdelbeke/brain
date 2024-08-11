```abc
X: 4
T: Ode to Joy (chat GPT)
M: 4/4
L: 1/4
K: C
E E F G | G F E D | C C D E | E D D2 |
E E F G | G F E D | C C D E | D C C2 |
D D E C | D E F E | C D E F | E D D2 |
```

## advanced
[source](https://garrettmassey.net/blog/writing-music-with-abcjs/)
```abc
T: Ode to Joy
M: 4/4
L: 1/4
K: C
%%staves {V1 V2}
V: V1 clef=treble
V: V2 clef=bass
[V: V1]|: B, B, C D | D C B, A, | G, G, A, B, | B,3/2 A,1/2 A,2 |
 B, B, C D | D C B, A, | G, G, A, B, | A,3/2 G,1/2 G,2:|
[V: V2]|: G, G, A, B, | B, A, G, ^F, | D, D, ^F, G, | G,3/2 ^F,1/2 ^F,2 |
 G, G, A, B, | B, A, G, ^F, | D, D, ^F, G, | ^F,3/2 D,1/2 D,2:|
```