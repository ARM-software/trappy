{% extends 'full.tpl'%}
{% block html_head %}
<script src="http://localhost:8080/EventPlot.js" type="text/javascript" charset="utf-8"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.6/d3.min.js", type="text/javascript" charset="utf-8"></script>
<script src="http://labratrevenge.com/d3-tip/javascripts/d3.tip.v0.6.3.js" type="text/javascript" charset="utf-8"></script>
<script src="https://cdn.rawgit.com/sinkap/a98037133fb79195583a1aa846671c22/raw/c23c231cbb1cdfe29eb84b1f786090a13c16dd93/EventPlot.js" type="text/javascript" charset="utf-8">
</script>
 {{ super() }}
{% endblock html_head %}
