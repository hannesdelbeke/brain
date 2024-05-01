If we [[file distribution|distribute]] unreal plugins separately from the main project, it would
- faster build speed
- faster [[unreal game sync|UGS]] sync speed
- not block builds on tool fail, leading to faster tool iteration & empowering non devs

potential drawbacks
- more complexity
- need a system to manage this
- dependency management needed
- different users could have different versions

questions
- is it worth the dev time?
- are we saving significant time?
- How much does this improve build speed.
- How much of a AAA project are optional [[unreal plugin]], vs project code & assets.
