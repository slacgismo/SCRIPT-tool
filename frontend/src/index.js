import React from "react";
import { render } from "react-dom";
import { BrowserRouter as Router, Route } from "react-router-dom";
import Overview from "./Components/Overview/Overview";
import Download from "./Components/Download/Download";
import AlgorithmPageLoadControl from "./Components/AlgorithmPage/AlgorithmPageLoadControl";
import AlgorithmPageLoadForecast from "./Components/AlgorithmPage/AlgorithmPageLoadForecast";
import AlgorithmPageCBA from "./Components/AlgorithmPage/AlgorithmPageCBA";
import About from "./Components/About/About";
import * as serviceWorker from "./ServiceWorker";

render(
    <Router>
        <Route exact path="/" component={Overview} />
        <Route exact path="/upload" component={Download} />
        <Route
            exact
            path="/alg-loadcontrol"
            component={AlgorithmPageLoadControl}
        />
        <Route
            exact
            path="/alg-loadforecast"
            component={AlgorithmPageLoadForecast}
        />
        <Route exact path="/alg-cba" component={AlgorithmPageCBA} />
        <Route exact path="/about" component={About} />
    </Router>,
    document.getElementById("root")
);

serviceWorker.unregister();
