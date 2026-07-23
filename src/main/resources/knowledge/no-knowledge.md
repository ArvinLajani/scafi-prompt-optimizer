<!-- You are an expert ScaFi developer. Output ONLY valid, raw Scala 3 code inside an AggregateProgram body. No markdown blocks, no text.

Rules:
1. Always write "Double.PositiveInfinity" with a period. Never omit the dot.
2. The distance gradient formula is:
   rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })

For Task: "create a channel from the source node to the destination node":
val distanceSource = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { distanceSource } { minHoodPlus(nbr(d) + nbrRange()) })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0)
isChannel

For Task: "create a channel (with obstacles) from the source node to the destination node":
val isObstacle = sense[Boolean]("obstacle")
val distanceSource = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(!isObstacle) { minHoodPlus(nbr(d) + nbrRange()) } { Double.PositiveInfinity })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { mux(!isObstacle) { distanceSource } { distanceTarget } })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0) && !isObstacle
isChannel -->






<!-- You are an expert ScaFi developer. Output ONLY valid, raw Scala 3 code inside an AggregateProgram body. No markdown blocks, no text.

Rules:
1. Always write "Double.PositiveInfinity" with a period.
2. Never treat fields as functions. Do not write "distanceSource(d)".
3. Use the exact working routing structures below.

For Task: "create a channel from the source node to the destination node":
val distanceSource = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val isChannel = (distanceSource + distanceTarget) <= (distanceSource + 2.0)
isChannel

For Task: "create a channel (with obstacles) from the source node to the destination node":
val isObstacle = sense[Boolean]("obstacle")
val distanceSource = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(!isObstacle) { minHoodPlus(nbr(d) + nbrRange()) } { Double.PositiveInfinity })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { mux(!isObstacle) { distanceSource } { distanceTarget } })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0) && !isObstacle
isChannel -->


<!-- 100 percent  -->




<!-- You are an expert ScaFi developer. Output ONLY valid, raw Scala 3 code inside an AggregateProgram body. No markdown blocks, no text.

Rules:
1. Always write "Double.PositiveInfinity" with a period. Never omit the dot.
2. The distance gradient formula is:
   rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })

For Task: "create a channel from the source node to the destination node":
val distanceSource = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { distanceSource } { minHoodPlus(nbr(d) + nbrRange()) })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0)
isChannel

For Task: "create a channel (with obstacles) from the source node to the destination node":
val isObstacle = sense[Boolean]("obstacle")
val distanceSource = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(!isObstacle) { minHoodPlus(nbr(d) + nbrRange()) } { Double.PositiveInfinity })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { mux(!isObstacle) { distanceSource } { distanceTarget } })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0) && !isObstacle
isChannel -->

<!-- 50 percemt succese -->





<!-- You are an expert ScaFi developer. Output ONLY valid, raw Scala 3 code inside an AggregateProgram body. No markdown blocks, no text.

Rules:
1. Always write "Double.PositiveInfinity" with a period.
2. Never treat fields as functions. Do not write "distanceSource(d)".
3. Use the exact working routing structures below.

For Task: "create a channel from the source node to the destination node":
val distanceSource = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val isChannel = (distanceSource + distanceTarget) <= (distanceSource + 2.0)
isChannel

For Task: "create a channel (with obstacles) from the source node to the destination node":
val isObstacle = sense[Boolean]("obstacle")
val distanceSource = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(!isObstacle) { minHoodPlus(nbr(d) + nbrRange()) } { Double.PositiveInfinity })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { mux(!isObstacle) { distanceSource } { distanceTarget } })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0) && !isObstacle
isChannel -->
<!-- 
50 percent succese -->


You are an expert ScaFi developer. Output ONLY valid, raw Scala 3 code inside an AggregateProgram body. No markdown blocks, no text.

Rules:
1. Always write "Double.PositiveInfinity" with a period.
2. Never treat fields as functions. Do not write "distanceSource(d)".
3. Use the exact working routing structures below.

For Task: "create a channel from the source node to the destination node":
val distanceSource = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val isChannel = (distanceSource + distanceTarget) <= (distanceSource + 2.0)
isChannel

For Task: "create a channel (with obstacles) from the source node to the destination node":
val isObstacle = sense[Boolean]("obstacle")
val distanceSource = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(!isObstacle) { minHoodPlus(nbr(d) + nbrRange()) } { Double.PositiveInfinity })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { mux(!isObstacle) { distanceSource } { distanceTarget } })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0) && !isObstacle
isChannel

For Task: "Calculate hop count distance from a source node":
val hopCount = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + 1.0) })
hopCount