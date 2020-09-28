# Multijoin Addon (pie menu)

press J:
* advanced_join
    compared to a simple join (vert_connect_path),
    it can also join vertices with no face between
    it can fill faces and merge vertices (threshold) 

press J and drag mouse to open the pie menu:
* multijoin
    need a last selected vertex. it can fill faces

* slide and join
    need 2 last verts
    it can fill faces and merge vertices (threshold)
    detail:
    select a subdivided edge (select 1 extremity press ctrl and select the other one)   
    and a second edge not subdvided (press shift and select the 2 last vertices)   
    it will subdivide the second edge with same amount of vertices and bridge   

* default join
    the join usually on J


N.B: for coders this addon registers a key and modifies another one   
and then inverse the process when unregistering.  

![](gif.gif)
