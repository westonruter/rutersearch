#!/usr/bin/perl -w
#########################################################
#        RuterSearch Entry Addition Program             #
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
use DBI;

print "Content-type: text/html\n\n";

sub htmlhead;
sub htmldtd;
sub htmlfoot;
sub trim;
sub backButton;
sub errorMsg;
sub reportError;
sub readQuery;
sub httpQueryVars;
sub htmlEntities;
sub getConfig;
sub putConfig;
sub openDatabase;
sub getFields;
sub closeDatabase;
sub cgidie;

my $database;
my $DBIgetAllEntries;
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
if($config{'restrictadd'} eq 'true' and (not $query{'password'} or lc $query{'password'} ne lc $config{'password'})){
	print &htmlhead('Addition Page Login');
	print <<HTMLCODE;
		<h1>Addition Page Login</h1>
		<form method="post" action="$ENV{'SCRIPT_NAME'}" name="frmLogin">
			Administration Password: <input type="password" name="password" size="20" value="$query{'password'}" />
			<input type="submit" value="Login" />
		</form>
		<script type="text/javascript">
		<!--
HTMLCODE
		print qq`			alert('"$query{'password'}" is an invalid password. Please try again...');` if exists $query{'password'} and (lc $query{'password'} ne lc $config{'password'});

print <<HTMLCODE;

			document.frmLogin.password.focus();
		//-->
		</script>
	</body>
</html>
HTMLCODE
	exit;
}



#Addition Results-----------------------------------------------------------------------------------
elsif($query !~ m/(?:title=|description=|url=|keywords=|author=)/ig){
	&openDatabase;

	open(ADDITIONPAGE, 'html/add.html') or &cgidie(&errorMsg("Error code 007: Unable to open 'add.html'") . &reportError('007') . &backButton);
	while(<ADDITIONPAGE>){
		if($config{'restrictadd'} eq 'true'){
			s/(<form.*?>)/$1\n<input type="hidden" name="password" value="$query{'password'}">/ig;
		}
		s/_totalentries_/$entryNumber/ig;
		print;
	}
	close ADDITIONPAGE;

	&closeDatabase;
	exit;
}



#Addition Results------------------------------------------------------------------------------------
else {
	&openDatabase;

	$query{'type'} ||= 'html';		#Make a guess
	$query{'author'} ||= '(author unknown)';#---/
	if(not $query{'title'}){
		&cgidie(&errorMsg('Please enter the title of the entry you wish to add.'), &backButton);
	}
	elsif(not $query{'url'}){
		&cgidie(&errorMsg('Please enter the url of the entry you wish to add.'), &backButton);
	}
	$query{'description'} ||= '';

	$query{'type'} = substr($query{'type'}, 0, 10);
	$query{'title'} = substr($query{'title'}, 0, 128);
	$query{'description'} = substr($query{'description'}, 0, 255);
	$query{'url'} = substr($query{'url'}, 0, 255);
	$query{'keywords'} = substr($query{'keywords'}, 0, 255);
	$query{'author'} = substr($query{'author'}, 0, 64);

	for(%entryFields = &getFields;   %entryFields;   %entryFields = &getFields){
		&cgidie(&errorMsg(qq`Error: An entry already has a title of "$query{'title'}". Please enter a variant of that title.`), &backButton) if(lc $entryFields{'title'} eq lc $query{'title'});
	}

	if(lc $config{'dbtype'} eq 'text'){	#if you are using a $config{'delimiter'} delimited text file
		open(DATABASE, ">>databases/$config{'dbfile'}") or &cgidie(&errorMsg("Error code 001: The $config{'dbtype'} database file 'databases/$config{'dbfile'}' cannot be accessed.") . &reportError("001") . &backButton);
		$config{'flock'} = 0 if $config{'flock'} and not eval { flock(DATABASE, 2); 1; };
		print DATABASE "$month/$dayOfMonth/$year $hour:$minute:$second" . $config{'delimiter'} . $query{'type'} . $config{'delimiter'} . $query{'title'} . $config{'delimiter'} . $query{'description'} . $config{'delimiter'} . $query{'url'} . $config{'delimiter'} . $query{'keywords'} . $config{'delimiter'} . $query{'author'} . "\n";
		close(DATABASE);
		flock(DATABASE, 8) if $config{'flock'};
	}

	elsif(lc $config{'dbtype'} eq 'mysql'){
		my $insertEntry = $database->prepare('INSERT INTO RUTERSEARCH VALUES (?,?,?,?,?,?,?)');
		$insertEntry->execute("$month/$dayOfMonth/$year $hour:$minute:$second", $query{'type'}, $query{'title'}, $query{'description'}, $query{'url'}, $query{'keywords'}, $query{'author'});
		$insertEntry->finish;
	}


	#Print the Addition results page
	open(ADDITIONRESULTS, 'html/additionresults.html') or &cgidi(&errorMsg("Error code 008: Error: Could not open 'html/additionresults.html'") . &reportError("008") . &backButtone());
	while(<ADDITIONRESULTS>){
		s/_totalentries_/$entryNumber/ig;
		s/_date_/$month\/$dayOfMonth\/$year $hour:$minute:$second/ig;
		s/_type_/$query{'type'}/ig;
		s/_title_/$query{'title'}/ig;
		s/_description_/$query{'description'}/ig;
		s/_url_/$query{'url'}/ig;
		s/_keywords_/$query{'keywords'}/ig;
		s/_author_/$query{'author'}/ig;
		print;
	}
	close(ADDITIONRESULTS);

	&closeDatabase;
	exit;
}



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
	if(lc($config{'dbtype'}) eq 'text') {		#If using a text database
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
	elsif(lc($config{'dbtype'}) eq 'mysql'){			#If using a MySQL database
		$database = DBI->connect(("DBI:mysql:$config{'mysqldbname'}"), $config{'mysqlusername'}, $config{'mysqlpassword'}) or &cgidie(&errorMsg("Error: Unable to connect to MySQL database.", &reportError(), &backButton));

		#Prepare statement to get each row containing array entries
		$DBIgetAllEntries = $database->prepare("SELECT * FROM rutersearch") or return 0;
		$DBIgetAllEntries->execute;
		$entryNumber = $DBIgetAllEntries->rows;
		&cgidie(&errorMsg("Error: The MySQL database has not been set up correctly."), &backButton) if $entryNumber < 0;
	}
	else {
			&cgidie( &errorMsg("Error code 002: Unknown database type. Must be set to 'MySQL' or 'text'."), &reportError("002"), &backButton );
	}
}

sub getFields {
	my $entryNumber = shift @_;
	my %fields = ();
	my($date, $type, $title, $description, $url, $keywords, $author) = ();
	my $textDBline = '';

	if(lc $config{'dbtype'} eq 'text'){
		$textDBline = <DATABASE>;
		return %fields if not $textDBline;
		chomp $textDBline;
		($date, $type, $title, $description, $url, $keywords, $author) = split(/$config{'delimiter'}/, $textDBline, 7);
	}
	elsif(lc $config{'dbtype'} eq 'mysql'){
		($date, $type, $title, $description, $url, $keywords, $author) = $DBIgetAllEntries->fetchrow_array;
		return %fields if $DBIgetAllEntries->errstr;
	}

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
	if(lc($config{'dbtype'}) eq 'text'){
		close DATABASE;
	}
	elsif(lc($config{'dbtype'}) eq 'mysql'){
		$DBIgetAllEntries->finish;
		$database->disconnect;
	}
}

sub cgidie {
	print join('', @_);
	exit;
	#return ((wantarray)? ('installed' => 'false')) : 0;
}
