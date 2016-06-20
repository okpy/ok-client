
auth_html = """
<html>
<head>
    <title>Okpy</title>
    <link href="http://ok-server.appspot.com/static/student/styles/auth.css" rel="stylesheet">
    {head}
</head>
<body>
<header>
    <div class="logo">
        <img src="http://ok-server.appspot.com/static/student/images/logo-light.png">
        <h1>Okpy</h1>
    </div>
    <nav>
        <ul>
            <li><a href="{site}">Dashboard</a></li>
        </ul>
    </nav>
</header>
<section class="top center-container" style="height:50%">
    <div class="center">
        <h1 class="title">{title}</h1>
        <h2 class="subtitle">{byline}</h2>
        <span class="break">
        <a href="{site}" class="button">Dashboard</a>
        <p class="copy">or <a href="http://cs61a.org/articles/using-ok.html">Read the FAQ</a></p>
        </span>
    </div>
</section>
<div class="rise status">{status}</div>
<section class="courses">
    <div class="wrap row" style="width:100%">
        {courses}
    </div>
</section>
<footer>
    <h3>okpy</h3>
    <p><a href="http://cs61a.org">cs61a.org</a> . <a href="http://composingprograms.com">composingprograms.com</a> . <a href="https://github.com/Cal-CS-61A-Staff/ok">github repo</a></p>
</footer>
</body>
<link href='https://fonts.googleapis.com/css?family=Roboto:400|Roboto+Condensed' rel='stylesheet'
      type='text/css'>
</html>
"""

partial_course_html = """
<div class="col-md-3" style="width: 30%;margin: 10px;">
    <div class="blob colored" color="blue">
        <div class="blob-main attn">
            <h2 class="blob-title ng-binding">{display_name}</h2>
            <p class="blob-shiftcopy blob-copy ng-binding"><span class="icon-tag"></span>{offering}</p>
        </div>
        <a href="https://okpy.org/{offering}">
            <div class="blob-action">View Course
                <span class="white arrow right"></span>
            </div>
        </a>
    </div>
</div>
"""

partial_nocourse_html = """
<div class="empty">
    <p>It looks like this email is not enrolled in any courses. Double-check to make sure that you submitted with the correct address.</p>
</div>
"""

red_css=  """
.top.center-container {
    background-color:rgb(239, 95, 86)
}

.top .center .button {
    background-color:rgb(171, 49, 44)
}
    .top .center .button:hover {
        background-color:#701d17
    }

.rise.status {
    background-color:#701d17;
}
"""
