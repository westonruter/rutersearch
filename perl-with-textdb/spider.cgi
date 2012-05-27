#!/usr/bin/perl -w
#########################################################
#        RuterSearch Webpage Spider Program             #
#          by Weston Ruter (RuterSoft)                  #
#          Copyright 2000                               #
#          http://www.Ruter.net/                        #
#########################################################
# All code is copyrighted by Weston Ruter (RuterSoft).  #
# You may not redistribute or resell this program       #
# without expressed written consent.                    #
#########################################################

#startfile

use strict;
use LWP::Simple;


print "Content-type: text/html\n\n";

sub htmlhead;
sub htmldtd;
sub htmlfoot;
sub trim;
sub backButton;
sub errorMsg;
sub reportError;
sub stripTags;
sub removeEntities;
sub parseHtml;
sub readQuery;
sub httpQueryVars;
sub htmlEntities;
sub getConfig;
sub putConfig;
sub openDatabase;
sub getFields;
sub closeDatabase;
sub cgidie;
sub parseDomain;
sub parseDir;
sub findHref;


my %entryFields = ();
my $entryNumber = 0;
my $query = &readQuery;
my %query = &httpQueryVars('text', $query);
my %hexQuery = &httpQueryVars('urlencoded', $query);
my %htmlQuery = &httpQueryVars('html', $query);
my %config = &getConfig('config.cgi');
my($second, $minute, $hour, $dayOfMonth, $month, $year) = localtime(time);
$month++;
$year += 1900;





if($config{'installed'} ne 'true'){
	&cgidie( &errorMsg('Error: RuterSearch is not installed. Remember to run administration to install.') );
}

#Enter Password----------------------------------------------------------------------------------------
if((not $query{'password'} or lc $query{'password'} ne lc $config{'password'}) and ($config{'restrictspider'} ne 'false')){
	print &htmlhead('Spider Login');
	print <<HTMLCODE;
		<h1>Spider Login</h1>
		<form method="post" action="$ENV{'SCRIPT_NAME'}" name="frmLogin">
			Administration Password: <input type="password" name="password" size="20" value="$query{'password'}" />
			<input type="submit" value="Login" />
		</form>
		<script type="text/javascript">
		<!--
HTMLCODE
		print qq`\t\t\talert('"$query{'password'}" is an invalid password. Please try again...');` if exists $query{'password'} and (lc $query{'password'} ne lc $config{'password'});

	print <<HTMLCODE;
		document.frmLogin.password.focus();
		//-->
		</script>
	</body>
</html>
HTMLCODE
	exit;
}
#Enter URL to parse
elsif(not $query{'url'}){
	print &htmlhead('Webpage Spider');
	print <<HTMLCODE;
		<h1>Webpage Spider</h1>
		<p>The RuterSearch Webpage Spider is a way to index and add many pages at once to your database. 
			When a URL is entered, the spider will visit that webpage and parse out all the links. It will then
			visit each of those and get the title, description, keywords, and author from the document. If no 
			description is supplied, the spider will try to make a meaningful description out of the body.
		</p>

		<form name="frmSpider" method="post" action="$ENV{'SCRIPT_NAME'}">
			<input type="hidden" name="password" value="$query{'password'}" />
			Webpage URL: <input type="text" name="url" size="30" /><br />
			<input type="checkbox" name="nowander" value="1" /> Only parse pages on supplied domain.<br />
			<input type="submit" value="Add Links to Database" />
		</form>
		<h3>Please be patient! This could take several minutes.</h3>
	</body>
</html>
HTMLCODE
}
else {

	#display results
	print &htmlhead('Webpage Spider Results');
	print "<h1>Webpage Spider Results</h1>";

	#load the page and parse out the links
	my $urlcontent = get($query{'url'});

	#Error: Unable to retrieve - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	if(not $urlcontent){
		print <<HTMLCODE;

		<p style="color:red;">Error: Unable to retrieve &quot;$query{'url'}&quot;</p>

		<form name="frmSpider" method="post" action="$ENV{'SCRIPT_NAME'}">
			<input type="hidden" name="password" value="$query{'password'}" />
			Webpage URL: <input type="text" name="url" size="30" value="$query{'url'}" />
			<input type="submit" value="Add Links to Database" />
		</form>
HTMLCODE
	}
	#Parse it, add it, and display it- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	else {
	   #Get the base href -  -  -  -  -  -  -  -  -  -  -  -
		my $basehref = '';
		my $thisdir = '';
		$urlcontent =~ /<base.+?href=(?:"|'|)([^"']*?)(?:"|'|\s|>)/im;
		$basehref = $1;
		my $entriesAdded = 0;

		if(not $basehref){
			$basehref = &parseDomain($query{'url'});
		}
		elsif(not &parseDomain($basehref)){
			if($basehref =~ m{^/}){
				$basehref = &parseDomain($query{'url'}) . $basehref;
			}
			else {
				$basehref = &parseDir($query{'url'}) . '/' . $basehref;
			}
		}

		#remove trailing /
		chop $basehref if substr($basehref, -1) eq '/';
		
		#What is this directory?
		$thisdir = &parseDir($query{'url'});


		#display page stats
		print "<ul>\n\t<li>Base href: $basehref</li>\n";
		print "\t<li>This path: $thisdir</li>\n";
		print "\t<li>Domain: " . &parseDomain($query{'url'}) . "</li>\n</ul>\n";

		#Get the all the titles
		&openDatabase;
		my %titles = ();
		for(my %entryFields = &getFields;   %entryFields;   %entryFields = &getFields){
			$titles{&trim($entryFields{'title'})} = 1;
		}



		#Parse out each <(a|area) href=""></a>	-  -  -  -  -  -	
		print "<ol>";
		for($urlcontent =~ /<(?:a|area).+?href=(?:"|'|)(.+?)(?:"|'|\s|>)/img){
			next if /^mailto:/i or /^javascript:/i;

			#put the URL in the right format
			my $url = &findHref($_, $thisdir, $basehref);

			#skip if not in this domain
			next if(exists $query{'nowander'} and (lc &parseDomain($query{'url'}) ne lc &parseDomain($url)) );

			#get the contents of the URL
			my($title, $description, $keywords, $author, $size) = &parseHtml($url);

			if(not $size){
				print qq`<p style="color:red">Error: Unable to load URL "$url".</p>`;
				next;
			}
			elsif(not $title){
				print qq`<p style="color:red">Error: Unable to get page title in "$url" (required).</p>`;
				next;	
			}
			elsif( $titles{&trim($title)} ){
				print qq`<p>Notice: Entry already exists with title of "$title".</p>`;
				next;
			}
			$entriesAdded++;
			$titles{&trim($title)} = 1;
			
				open(DATABASE, ">>databases/$config{'dbfile'}") or &cgidie(&errorMsg("Error code 001: The $config{'dbtype'} database file 'databases/$config{'dbfile'}' cannot be accessed.") . &reportError("001") . &backButton);
				$config{'flock'} = 0 if $config{'flock'} and not eval { flock(DATABASE, 2); 1; };
				print DATABASE "$month/$dayOfMonth/$year $hour:$minute:$second" . $config{'delimiter'} . 'html' . $config{'delimiter'} . $title . $config{'delimiter'} . $description . $config{'delimiter'} . $url . $config{'delimiter'} . $keywords . $config{'delimiter'} . $author . "\n";
				close(DATABASE);
				flock(DATABASE, 8) if $config{'flock'};

				print "<li><b>$title</b></li>";
				print '<ul>';
					print "<li>Description: $description</li>";
					print "<li>URL: $url</li>";
					print "<li>Keywords: $keywords</li>";
					print "<li>Author: $author</li>";
				print '</ul>';
		}
		print "</ol>";


		&closeDatabase;

		print "<h2>Added $entriesAdded entries to Database</h2>";


	}
	print "\n\t</body>\n</html>\n";
}

#my @parts = &parseHtml($ARGV[0]);
#print "title = $parts[0]\n";
#print "description = $parts[1]\n";
#print "url = $parts[2]\n";
#print "keywords = $parts[3]\n";
#print "author = $parts[4]\n";

#Subroutines-------------------------------------------------------------------------------------------------------------



sub htmlhead {
	return <<HTMLCODE;
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
	<head>
		<title>$_[0]</title>
		<style type="text/css">
			body,td,h1,h2,h3,h4,p,ul,ol,li,input {
				font-family:Veranda,Arial,Helvetica,Serif;
			}
		</style>
	</head>
	<body>
HTMLCODE
}

sub htmldtd {
	my $request = shift;
	if('transitional' =~ /\Q$request\E/i){
		return qq`<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n\t"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n`;
	}
	elsif('strict' =~ /\Q$request\E/i){
		return qq`<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n\t"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n`;
	}
	elsif('frameset' =~ /\Q$request\E/i){
		return qq`<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN"\n\t"http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n`;
	}
	else {
		return &errorMsg("Wrong DTD");
	}
}

sub htmlfoot {
	return "\n</html>\n" . 
	'';
}

sub trim {
	my $string = shift;
	return $string if not $string;	
	$string =~ s/\s+/ /g;
	$string =~ s/^ //;
	$string =~ s/ $//;
	return $string;
}

sub backButton {
	return("<br><div align=\"center\" style=\"font-size:20pt; \"><a href=\"javascript:history.go(-1)\">&lt; Go Back</a></div>");
}

sub errorMsg {
	return("<div align=\"center\" style=\"color:red; font-weight:bold;\">$_[0]</div>");
}

sub reportError {
	#$_[0] is the error code
	return("<div align=\"center\" style=\"font-size:20pt; \">Report error to <a href=\"mailto:$config{'email'}?subject=Error code $_[0]\">search administrator</a></div>");
}

sub stripTags {
	my $string = shift;
	$string =~ s/<script(.|\n)*?\/script>//gim;
	$string =~ s/<style(.|\n)*?\/style>//gim;
	$string =~ s/<!--(.|\n)*?-->//gim;
	$string =~ s/<(.|\n)*?>//gim;
	return $string;
}

sub removeEntities {
	my $string = shift;
	$string =~ s/&nbsp;/ /gim;
	$string =~ s/&quot;/"/gim;
	$string =~ s/&amp;/&/gim;
	return $string;
}

sub parseHtml {
	my($title, $description, $url, $keywords, $author) = '';
	$url = shift @_;
	my $pagesource = get $url;
	my($name,$content,$body,$paragraph,$pagesize) = '';
	my @metamatches = ();

	$pagesize = length $pagesource;
	$pagesource =~ m{<title>([^<>]+?)</title>}im;
	$title = &trim($1);

	@metamatches = ($pagesource =~ m{<meta\s+name=("|')(.*?)\1\s+content=("|')(.*?)\3}img);
	for(my $i = 0; $i < @metamatches; $i += 4){
		my($name, $content) = ($metamatches[$i+1], $metamatches[$i+3]);
		$description = $content if lc $name eq 'description';
		$keywords = $content if lc $name eq 'keywords';
		$author = $content if lc $name eq 'author';
	}

	if(not $description){
		$pagesource =~ m{<body(?:.|\n)*?>((?:.|\n)*?)</body>}img;
		$description = substr(&removeEntities(&trim(&stripTags($1))), 0, 250);
	}
	$author ||= '(author unknown)';

	return (&trim($title), &trim($description), &trim($keywords), &trim($author), $pagesource);
}

sub readQuery {
	my $string = '';
	if($ARGV[0]) {
		$string = $ARGV[0];
	}
	elsif($ENV{'REQUEST_METHOD'} eq 'GET'){	#method='get'
		$string = $ENV{'QUERY_STRING'};
	}
	elsif($ENV{'REQUEST_METHOD'} eq 'POST') {
		read(STDIN, $string, $ENV{'CONTENT_LENGTH'});	#method='post'
	}
	return $string;
}

sub httpQueryVars {
	#Either "text", "html", "urlencoded", or none
	my $query = pop @_;
	my $type = lc pop(@_);
	my $pair = '';
	my(%query,%hexQuery,%htmlQuery) = ();

	#$query =~ s/%0D%0A/\n/gi;

	#Parse and set the query variables into %query and %hexQuery
	foreach $pair (split(/&/, $query)){				#Cycle through each value pairs
		my($key, $value) = split(/=/, $pair);		#Separate name and value
		$key =~ tr/+/ /;
		$key =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		$hexQuery{lc($key)} = $value;	  	#Assign URL encoded variable to a %hexQuery variable
		next if $type eq 'urlencoded';
		$value =~ tr/+/ /;
		$value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
		$query{lc($key)} = $value;		#Assign name and varible to a hash variable
		next if $type eq 'text';
		$htmlQuery{lc($key)} = scalar &htmlEntities($value);
	}

	return %query if $type eq "text";
	return %hexQuery if $type eq "urlencoded";
	return %htmlQuery if $type eq "html";
}

sub htmlEntities {
	my(@array) = ();
	my(@items) = @_;

	for(@items){
		s/&/&amp;/g;
		s/"/&quot;/g;
		s/'/&#39;/g;
		s/</&lt;/g;
		s/>/&gt;/g;
		push(@array, $_);
	}

	return @array if(scalar(@items) > 1);
	return $array[0] if(scalar(@items) == 1);
}

sub getConfig {
	my %config = ();
	local *FILE;

	if(not(-e($_[0]))){
			&cgidie( &errorMsg(qq`Error: $_[0] not found.`) );
	}
	elsif(not open(FILE, $_[0])){
		return ('installed' => 'false');
	}
	else {
		for(<FILE>){
			chomp;
			my @parts = split(/=/, $_, 2);
			next if not $parts[0];
			$config{lc $parts[0]} = $parts[1];
		}
		close FILE;
		return %config;
	}
}

sub putConfig {
	my $file = shift(@_);
	my %config = @_;
	my $flockwork = 1;
	local *CONFIG;

	open(CONFIG, ">$file") or &cgidie( &errorMsg("Error: Could not write to $file.") );
	$flockwork = 0 if not eval { flock(CONFIG, 2); 1; };
	while(my($key, $value) = each(%config)){
		print CONFIG "$key=$value\n";
	}
	flock(CONFIG, 8) if $flockwork;
	close(CONFIG);

}


sub openDatabase {
		if(not -e "databases/$config{'dbfile'}"){
			&cgidie( &errorMsg("Error code 001: The $config{'dbtype'} database file 'databases/$config{'dbfile'}' cannot be found."), &reportError("001"), &backButton );
		}
		open(DATABASE, "databases/$config{'dbfile'}") or &cgidie(&errorMsg("Error: Unable to open the database."), &reportError("001"), &backButton);
		my $buffer = '';
		while(sysread DATABASE, $buffer, 4096){
			$entryNumber += ($buffer =~ tr/\n//);
		}
		close DATABASE;

		open(DATABASE, "databases/$config{'dbfile'}"); 
}

sub getFields {
	my $entryNumber = shift @_;
	my %fields = ();
	my($date, $type, $title, $description, $url, $keywords, $author) = ();
	my $textDBline = '';

		$textDBline = <DATABASE>;
		return %fields if not $textDBline;
		chomp $textDBline;
		($date, $type, $title, $description, $url, $keywords, $author) = split(/$config{'delimiter'}/, $textDBline, 7);

	%fields = (
		'date' => $date,
		'type' => $type,
		'title' => $title,
		'description' => $description,
		'url' => $url,
		'keywords' => $keywords,
		'author' => $author,
	);
	return %fields;
}

sub closeDatabase {
		close DATABASE;
}

sub cgidie {
	print join('', @_);
	exit;
	#return ((wantarray)? ('installed' => 'false')) : 0;
}

sub parseDomain {
	my $url = shift;
	my $domain = '';
	
	if($url =~ m[^((?:http|ftp)://[^/]+)(?:/|$)]i){
		$domain = $1;
	}
	else {
		return '';
	}

	return $domain;
}

sub parseDir {
	my $url = shift;
	my $dir = '';
	
	if(&parseDomain($url) eq $url){
		return $url;
	}
	elsif($url =~ m[^(.+?)/[^/]*$]i){
		$dir = $1;
	}
	else {
		return undef;
	}

	return $dir;
}

sub findHref {
	my $href = shift;
	my $thisdir = shift;
	my $basehref = shift;

	return $href if($href =~ m{^(?:http|ftp)://}i);

	while($href =~ m{\.\./}){
		$href =~ s{\.\./}{};
		$thisdir =~ s{/\w+$}{};
	}
	$href =~ s{\./}{}g;

	if(substr($href, 0, 1) eq '/'){
		$href = $basehref . $href;		
	}
	elsif($thisdir =~ m/\Q$basehref\E/){
		$href = $thisdir . '/' . $href;
	}
	else {
		$href = $basehref . '/' . $href;
	}
	$href =~ s/#.*$//;
	return $href;
}
