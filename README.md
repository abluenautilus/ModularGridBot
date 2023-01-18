This bot queries modulargrid to retrieve information about eurorack modules. 

Once the bot is installed on your server, to use it, you type the name of the maker and module within double brackets, like this: 

[[Mutable Instruments Beads]]

If there's an exact match on the modulargrid site, meaning a page with the title "mutable-instruments-beads" it will take you right there. Otherwise, the bot will use the modulargrid search function, and return the best result when sorting the results by popularity. This search can yield unexpected results if your search term is too vague, but something like 

[[Beads]]

will probably work. 

If you want to retreive the top few results, you can include a colon followed by a number, so

[[Mutable Instruments: 5]]

will return the top 5 results when searching for "mutable instruments", again sorted by popularity. 