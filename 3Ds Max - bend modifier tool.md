Often, when [[modular]] assets are created, they are made to fit on a power of 2 grid size, so they are easy to snap together in the [[game engine]].  
But when creating curved pieces, it's not easy to bend it to fit [[exact|exactly]] on the grid. It's a manual tweak process, requiring the manual snapping of [[vertex|vertices]] on the grid.

A hack that makes this easier, involves the multiplying of the bend modifier pivot with `86.0576519035213`, but nobody understood why this hack worked.
Let's figure it out

## 86.0576519035213 EXPLAINED
**and why it's actually wrong**

> [!NOTE]- context
> When asking around for ideas for cool tools to make, [[Sjoerd De Jong]] told me about a problem he had with the bend modifier in [[Autodesk 3ds Max]]. He always had to fix it manual which was tedious. When applying a bend modifier on a prop with a power of 2 height, the end results width was not dividable by 2 and thus not on the grid (UDK grid, every 8 units) However Sjoerd found a [solution](http://www.hourences.com/maxmaya-bending-of-modular-meshes/) which he posted on his site
>
>>[!QUOTE] [Sjoerd](http://www.hourences.com/maxmaya-bending-of-modular-meshes/)
>> When you got modular on grid meshes in Max/Maya, and you bend them 90/180/270 degrees, their ends are never ever on grid, even though the original mesh was perfectly on grid. Most people, that included me, would in that case manually move the vertices on one end and snap them to the grid. That gets very tedious to do very fast though.
>> I just found out that if you take the length of the mesh, divided by exactly 86.0576519035213, and then take the result of that division and use that to offset the center of the bend deform with into the opposite direction the mesh bends, then the end of that mesh will be exactly on grid! So for example, a 1024 long mesh that bends needs to have its bend pivot point offset by 11.899 units and it will end up exactly on the grid.
> 
> So I decided to give this a test in [[Autodesk 3ds Max|3ds Max]]. After applying the bend modifier I saw that indeed, the last vertex did not ended on a power of 2 grid. So I tried Sjoerd his fix.  
> 
> ![[3Ds Max - bend modifier tool-1749202657966.jpeg|200]]
> 
> $$ \frac{1024}{86.0576519035213} = 11.899 $$
> After offsetting with `11.899` the width was `640`, Success!
> 
> I asked Sjoerd where he got the number, but he couldn’t remember. And no one on the internet knew why `86.0576519035213` gave that result. But it worked, so I just accepted it and decided to make a script for it.
> 
> However, after creating a script that added the correct offset based on the direction and the angle, I discovered it only worked for 90 degree angles. The angles 180,270 and 360 didn't end up on the grid. Did I make a mistake?
> 
>  I tried various sizes and tried to do it manual, but it all gave the same result.  
> `86.0576519035213` wasn’t the perfect number after all.
>   
> If I wanted to make it work for all angles , I had to figure out why dividing by `86.0576519035213 `gave the correct result for 90 degree angles.
> 

I assumed the bend modifier tried to keep the same distance on the arc of the circle.  
If this was true, I knew I would be able to find a way, else I would make the script only for 90 degrees.  

If the bend modifier acts like a circle from its pivot, we can say that the width of our bend mesh is the radius of a circle/
$$
\begin{align}
\text{width} &= \text{radius} & w &= r
\end{align}
$$

let's calculate the circumference `O` of a circle
$$
                             O_{circle} = 2 π r
$$
  
We only have a 90 degree angle, since a full circle is 360, our circumference is 1 fourth.

$$
O_{circle} = 4 O_{90-degrees} 
$$
When we bend a mesh, the height of the mesh becomes the circumference of the 90 degree.
For height (`h`) of the mesh:
$$
                             O_{circle} = 4 h
$$
If we equal both O formula
$$
4 h = 2 π r
$$we can rewrite this as
$$ r = \frac{2h}{\pi} $$

When we fill in our values we see that the formula is correct
$$ r = \frac{2 \times 1024}{\pi} = 651.89868 $$

Now that we know how to calculate the radius, we can use this to calculate in the reverse order.

From Sjoerds method we know that we have to move the center of the bendmodifier.  
Since we move it in the opposite direction,  this is the same as making the initial radius smaller.  
This means we subtract, or add a negative number to the initial radius.  
This is where it gets confusing:  
we have the initial bad radius : `651.89868` and the final radius : `640  `
when we move the center with the correct offset  we get the final radius : 
$$ r_f = \text{final radius} $$
$$ r + \text{offset} = r_f $$
$$ \text{offset} = r_f - r $$
Testing this in 3ds Max  
We have a 1024 high cube, which results in a 651.89868 radius  
lets try to make this into a 512 radius:

$$ r_f = r + \text{offset} = 651.89868 + (-11.899) = 640 $$
I've added parentheses around the negative number to keep the notation clear. This ensures proper readability in mathematical formatting. Let me know if you need any refinements!

With this confirmed we now know how to calculate the correct offset with the radius.  
Since we also know how to calculate the radius, we can put them together:

$$ \text{offset} = r_{final} - r = r_{final} - \frac{2h}{\pi} $$
Using this formula we can choose any final radius and get it´s offset.  
This is still only for 90 degrees, but using this we can easily get the other degrees their formula.

But one question remains unanswered, why did the number 86.0576519035213 work for 90 degrees? Now that we have the formula to calculate any radius, and sjoers original formula, we can find out. Let us pretend we don’t know this constant, and want to calculate it.
$$ c = \text{constant} $$
$$ \frac{h}{c} = \text{offset} $$
$$ r + \text{offset} = r_f $$
$$ \frac{2h}{\pi} + \frac{h}{c} = r_f $$
$$ \frac{h}{c} = r_f - \frac{2h}{\pi} $$
$$ c = \frac{h}{r_f - \frac{2h}{\pi}} $$
Let´s put our values in there and use wolfram to calculate the most exact possible result  
the final radius Sjoerd had as result was 640 for a 1024 height, and 320 for a 512
                             $$ c = \frac{1024}{640 - \frac{2 \times 1024}{\pi}} = -86.0602056878460272632506284428750874459128685735009 $$
This is very close to our original number, is it just coincidence?
$$ c = \frac{512}{320 - \frac{2 \times 512}{\pi}} = -86.0602056878460272632506284428750874459128685735009 $$
No coincidence. And we can easily see in the formula that they just multiply all elements with 2, which cancel each other, thus always leading to the same result. Since the relationship between 1024 / 620 and 512 / 320 is constant, we can simplify this to 8 and 5. The height is always a power of 2, and the end result width a multiplication of 5 and 2

So to come back on our question, why did 86.0576519035213 work and how did someone found it? It works because it is almost the same as our result so it gives the same result if using it to calculate the offset, since floating points get rounded on the computer. 

And how did someone find it? I guess through trial and error, since it is not the exact constant.

Now that we know the formula we don’t need the number anymore, however we still have the option to use it, or can calculate the correct number for the other angles.

> [!NOTE]- 180 degrees
> In a 180 degree bend the width is 2 times the radius, and half of the circumference is the height:
> $$ O = 2r\pi = 2h $$
> $$ \frac{O}{2} = r\pi = h $$
> $$ r = \frac{h}{\pi} $$
> $$ 2r = \text{width} = \frac{2h}{\pi} $$
> Here we get the same formula as before again, even though the width proportion to the radius changed, the height changed in a similar way countering each other.
> 
> Let´s now calculate the offset. The offset is how much we move the center. Since the width is 2 times the radius, the width will be detracted with 2 times the offset.
> $$ 2r + 2 \times \text{offset} = \text{width} $$
> $$ \text{offset} = \frac{\text{width} - 2r}{2} $$
> $$ \text{offset} = \frac{\text{width}}{2} - \frac{h}{\pi} $$
> The offset formula is half of the 90 degree offset formula.
> for constant `c`
> $$ \frac{h}{c} = \text{offset} $$
> $$ 2r + 2 \times \text{offset} = \text{width} $$
> $$ \frac{2h}{\pi} + \frac{2h}{c} = \text{width} $$
> $$ \frac{2h}{c} = \text{width} - \frac{2h}{\pi} $$
> $$ c = \frac{h}{\frac{\text{width} - \frac{2h}{\pi}}{2}} $$
> The constant formula is half of the 90 degree constant formula.

> [!NOTE]- 270 degrees
> Since it contains 3 parts, it does not nicely divide by 2. The height is 3 fourth of the circumference. The width is 2 times the radius. So we can use the 180 degree formula and input height/3*2 as the height.  
> $$ O = 2 \pi r $$
> $$ \frac{O}{4} \times 3 = h $$
> $$ h = \frac{2 \pi r}{4 \times 3} $$
> $$ h = \frac{3 \pi r}{2} $$
> $$ r = \frac{2h}{3\pi} $$
> $$ \text{width} = 2r $$
> $$ \text{width} = \frac{4h}{3\pi} $$
> $$ 2r + 2 \times \text{offset} = \text{width} $$
> $$ \text{offset} = \frac{\text{width} - 2r}{2} $$
> $$ \text{offset} = \frac{\text{width}}{2} - \frac{2h}{3\pi} $$
> for constant `c`
> $$ \frac{h}{c} = \text{offset} $$
> $$ 2r + 2 \times \text{offset} = \text{width} $$
> $$ 2 \times \text{offset} = \text{width} - 2r = \text{width} - \frac{2h \times 3}{2\pi} $$
> $$ \frac{2h \times 3}{2\pi} + \frac{2h}{c} = \text{width} $$
> $$ \frac{h \times 3}{\pi} + \frac{2h}{c} = \text{width} $$
> $$ c = \frac{2h}{\text{width} - \frac{h \times 3}{\pi}} $$
> 
> Testing this in 3ds Max shows us that using the constant to get a nice multiplication of 5 and 2 changes the size quite a lot. Since there is such a big difference between the initial and final radius it would be wiser to solve it in a different way. For example divide by a power of 2 and remove the remainder, then use the quotient and multiply it back with the power of 2 that you used.  
> To get even less deformation, round the remainder up and add one to the quotient if the remainder is more than half of the power of 2.
> 
> I would even suggest this method for every other degree since it is more accurate and adapts to the grid size, giving the user more control over his modular pieces.

> [!NOTE]- 360 degrees
> The height is the same as the circumference. The width is 2 times the radius, just like the 180 degrees. This means we can input half of our height in the 180 degree formula to get the result, and this also means the constant is halved again.
> 
> `-21.5150514219615068158126571107187718614782171433752`

## Conclusion
Now knowing all of this, it easy to automate the whole process! This will make creating modular curved pieces much easier for the artist, which was my final goal. 

This was quite different from my usual process, which barely uses [[mathematics]] and is more pure scripting and automating. I decided to write down my though process, so people can understand why this number was used and how they can use it for their own solutions.

You can download my [[3ds max tool]] [here](<[http://www.scriptspot.com/3ds-max/scripts/advanced-bend-modifier](http://www.scriptspot.com/3ds-max/scripts/advanced-bend-modifier)>) for easy bends in 3ds Max.

[[calculations]]