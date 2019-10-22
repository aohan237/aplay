# aplay
[![Downloads](https://pepy.tech/badge/aplay)](https://pepy.tech/project/aplay)
[![PyPI version](https://badge.fury.io/py/aplay.svg)](https://badge.fury.io/py/aplay)

## **python actor model(live in a Play,LOL) implement using asyncio**


### Install

--------------

pip install aplay


### Usage

refer to the example dirs

#### instructions
    KernelActor means the kernel to start or daemon the whole program. 
    it is only one process,you will have to use multiprocess if you want to utilize multi cores.

    Actor is the basic class for worker actor and the kernel.

    for worker actor ,you only need to inherit this class and define your funcion that needed. 

#### Actor Api table

##### property
name|description|useage
-|-|-
_name|actor's name|for identitify the actor
_mailbox|actor's mailbox|the mailbox to store message
_child|actor's children (instances of actor)|the actors start by itself
_runing_state|actor's running state|state the running state of the actor
_human_runing_state|stopped by human|for manually stop the actor and by default ,it cant be started by its parent
_parent|actor's parent actor|actor's parent
_kernel|actor's kernel|the daemon kernel of the actor
_address｜the actor's address from the kernel| the actor' address
_loop|actor's loop|actor's loop

##### functions need to inderited

function name|usage|must|description|default
-|-|-|-|-
decide_to_start|decide to start itself|not| to decide itself start or not. actor can be in any state.  you can implement this function to make your own decision|only human stopped state can prevent the actor starting.
user_task_callback|task done callback|not|the callback of a task. can be with success and exception msg. | do nothing
prepare_children|prepare to create or get the child actor|not|if you need child actor,you must inplement this, and add your child actor creator in here| do nothing
prepare_mailbox|prepare the mailbox|not| if you want to define your own async mailbox or use redisMailbox|do nothing
msg_handler|the working function|yes|the only funcion that really do the jobs| not Implement

##### tips
    actors are defined in class. you can create lots of actors in one actor.
    but do not Circular create actors. 
    such as you have a A_actor and B_actor,A_actor creates lots of B_actor, and B_actor creates lots of A_actor.

    you can define lots of B_actor from A_actor with different names. and these actors can do lots of work based on different msg types

### why this lib

this lib intends to Decoupling the work flow using actor-like system,which utilize the asyncio to make work efficiently.

we dont define the msg format just for you have the freedom to adjust to your program. it is you to guarantee your msg format's complete.

the commong workflow is **single-forward**, just as follows:

say you have A-actor,B-actor,C-actor:

A-actor work done then transfer msg to B-actor then to C-actor. no backwards.


Requirements
------------

* Python_ 3.5+  https://www.python.org

License
-------

The aplay is offered under MIT license.
