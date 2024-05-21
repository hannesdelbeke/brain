There is a slight difference in the channels. The green channel is usually slightly higher precision than the red and blue channels (red and blue get 5 bits of data while green gets 6 bits, making a nice ring 16bits for all 3 together - that plays nicely with memory access). Alpha generally gets a full 8 bits.

The reasoning being that human eyes are most sensitive to green light so if you need to split 16 bits across 3 components, green should be the one that gets the extra bit.

[[texture]]