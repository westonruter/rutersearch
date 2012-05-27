#!/usr/bin/perl -w
#########################################################
#        RuterSearch Core Program                       #
#          by Weston Ruter (RuterSoft)                  #
#          Copyright 2001                               #
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

sub cgidie;
sub trim;
sub addStyleWordTags;
sub stripTags;
sub backButton;
sub errorMsg;
sub reportError;
sub wordSearch;
sub readQuery;
sub httpQueryVars;
sub htmlEntities;
sub getConfig;
sub putConfig;
sub syntax;
sub openDatabase;
sub getFields;
sub closeDatabase;

my $startStyle = "\xC9";
my $endStyle = "\xBB";

my $database;	#MySQL database object
my $DBIgetAllEntries;
my %entryFields = ();
my $entryNumber = 0;
my %fields = ();
my $filler = 0;
my $i = 0;
my $isNextPage = '';
my $isPreviousPage = '';
my %matches = ();
my $nextPageUrl = '';
my $originalRegExMatch = '';
my $pagesOfResults = 1;
my $previousPageUrl = '';
my @queryWords = ();
my $regExMatch = '';
my $requiredWord = '';
my $resultNumber = 0;
my @results = ();
my @resultTemplate = ();
my $searchResults = '';
my $stop = 1;
my $thekey = '';
my %unsortedResults = ();
my $urlNoPage = '';
my $query = &readQuery;

my %query = &httpQueryVars('text', $query);
my %hexQuery = &httpQueryVars('urlencoded', $query);
my %htmlQuery = &httpQueryVars('html', $query);
my %config = &getConfig('config.cgi');

if($config{'installed'} ne 'true'){
	&cgidie( &errorMsg('Error: RuterSearch is not installed. Remember to run administration to install.') );
}

#Get the time
my($second, $minute, $hour, $dayOfMonth, $month, $year) = localtime(time);
$month++;
$year += 1900;

#Open the database, assign values into @results
&openDatabase;

#Search page (search.html) ----------------------------------------------------------------------------------------------
if(not $query{'string'}){		#If no search query
	open(SEARCHPAGE, 'html/search.html') or &cgidie(&errorMsg("Error code 003: Could not open the search page (html/search.html)"), &reportError('003'), &backButton);
	while(<SEARCHPAGE>){
		s/_totalentries_/$entryNumber/ig;
		print;
	}
	close SEARCHPAGE;
	&closeDatabase;
	exit;
}





#Variable creation and manipulation-----------------------

$query{'page'} ||= 1;						#If user did not specify result page
$query{'type'} ||= $config{'resulttype'};			#If user did not specify type, use type from config
$query{'stylewords'} ||= $config{'stylewords'};		#If user did not specify styling the words
$query{'perpage'} ||= $config{'perpage'};			#If user did not specify results per page
if(lc $query{'perpage'} eq 'all' or not $query{'perpage'}){	#If user wanted to display all results
	$query{'perpage'} = $entryNumber;
}

#Url of page without 'page'
$urlNoPage = ($ENV{'SCRIPT_NAME'} . 
	'?string=' . $hexQuery{'string'} . 
	'&type=' . $hexQuery{'type'} . 
	'&perpage=' . $query{'perpage'} . 
	'&stylewords=' . $query{'stylewords'}
);


#########################################
#Syntax Engine - parse the search query ############################################################
#########################################

#Define variables for words
$queryWords[0]{'t'} = ();
$queryWords[0]{'d'} = ();
$queryWords[0]{'u'} = ();
$queryWords[0]{'k'} = ();
$queryWords[0]{'a'} = ();
$queryWords[0]{'X'} = ();

$queryWords[1]{'t'} = ();
$queryWords[1]{'d'} = ();
$queryWords[1]{'u'} = ();
$queryWords[1]{'k'} = ();
$queryWords[1]{'a'} = ();
$queryWords[1]{'X'} = ();

$queryWords[2]{'t'} = ();
$queryWords[2]{'d'} = ();
$queryWords[2]{'u'} = ();
$queryWords[2]{'k'} = ();
$queryWords[2]{'a'} = ();
$queryWords[2]{'X'} = ();



&syntax('title');			#Parse the words from title()
&syntax('description');		#Parse the words from description()
&syntax('url');			#Parse the words from url()
&syntax('keywords');		#Parse the words from keywords()
&syntax('author');		#Parse the words from author()
&syntax('X');			#Parse the words that are not in a restrictor

#print join(", ", @{$queryWords[0]{'t'}}), "<br>\n";
#print join(", ", @{$queryWords[0]{'d'}}), "<br>\n";
#print join(", ", @{$queryWords[0]{'u'}}), "<br>\n";
#print join(", ", @{$queryWords[0]{'k'}}), "<br>\n";
#print join(", ", @{$queryWords[0]{'a'}}), "<br>\n";
#print join(", ", @{$queryWords[0]{'X'}}), "<br>\n";

#print join(", ", @{$queryWords[1]{'t'}}), "<br>\n";
#print join(", ", @{$queryWords[1]{'d'}}), "<br>\n";
#print join(", ", @{$queryWords[1]{'u'}}), "<br>\n";
#print join(", ", @{$queryWords[1]{'k'}}), "<br>\n";
#print join(", ", @{$queryWords[1]{'a'}}), "<br>\n";
#print join(", ", @{$queryWords[1]{'X'}}), "<br>\n";

#print join(", ", @{$queryWords[2]{'t'}}), "<br>\n";
#print join(", ", @{$queryWords[2]{'d'}}), "<br>\n";
#print join(", ", @{$queryWords[2]{'u'}}), "<br>\n";
#print join(", ", @{$queryWords[2]{'k'}}), "<br>\n";
#print join(", ", @{$queryWords[2]{'a'}}), "<br>\n";
#print join(", ", @{$queryWords[2]{'X'}}), "<br>\n";

##############################################################
#   Time to do the real searching (the beef) of the program  ############################################################
##############################################################


$matches{'title'} = 0;
$matches{'description'} = 0;
$matches{'url'} = 0;
$matches{'keywords'} = 0;
$matches{'author'} = 0;

#Set the filler for the end of the key in order to sort (since Perl sorts by strings and not numbers)
$filler = (1 . '0' x length $entryNumber) + $entryNumber;

#Go through each entry in the database and add it to the results if it matches
for(%entryFields = &getFields;   %entryFields;   %entryFields = &getFields){	#Get the next results in replace of $i
	$stop = 0;		#If it wasn't matched
	if(lc $query{'type'} eq lc $entryFields{'type'}){		#If it is the correct file type
		if($queryWords[0]{'X'}){
			&wordSearch(@{$queryWords[0]{'X'}}, 'title');
			&wordSearch(@{$queryWords[0]{'X'}}, 'description');
			&wordSearch(@{$queryWords[0]{'X'}}, 'url');
			&wordSearch(@{$queryWords[0]{'X'}}, 'keywords');
			&wordSearch(@{$queryWords[0]{'X'}}, 'author');
		}
		if($queryWords[0]{'t'}){ &wordSearch(@{$queryWords[0]{'t'}}, 'title') }
		if($queryWords[0]{'d'}){ &wordSearch(@{$queryWords[0]{'d'}}, 'description') }
		if($queryWords[0]{'u'}){ &wordSearch(@{$queryWords[0]{'u'}}, 'url') }
		if($queryWords[0]{'k'}){ &wordSearch(@{$queryWords[0]{'k'}}, 'keywords') }
		if($queryWords[0]{'a'}){ &wordSearch(@{$queryWords[0]{'a'}}, 'author') }

		#Required words:	
		if($queryWords[1]{'X'}){
			my $check = 0;
			foreach $requiredWord (@{$queryWords[1]{'X'}}){
				if(&wordSearch($requiredWord, 'title') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'description') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'url') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'keywords') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'author') == 2){ $check++; }

				if(not $check){
					$stop++;
					last;
				}
				else {
					$check = 0;
				}
			}
		}
		$stop++ if($queryWords[1]{'t'} and not $stop and (&wordSearch(@{$queryWords[1]{'t'}}, 'title') !=  2));
		$stop++ if($queryWords[1]{'d'} and not $stop and (&wordSearch(@{$queryWords[1]{'d'}}, 'description') != 2));
		$stop++ if($queryWords[1]{'u'} and not $stop and (&wordSearch(@{$queryWords[1]{'u'}}, 'url') != 2));
		$stop++ if($queryWords[1]{'k'} and not $stop and (&wordSearch(@{$queryWords[1]{'k'}}, 'keywords') != 2));
		$stop++ if($queryWords[1]{'a'} and not $stop and (&wordSearch(@{$queryWords[1]{'a'}}, 'author') != 2));


		#Required not words:	
		if($queryWords[2]{'X'} and not $stop){
			my($check) = 0;
			foreach $requiredWord (@{$queryWords[2]{'X'}}){
				if(&wordSearch($requiredWord, 'title') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'description') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'url') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'keywords') == 2){ $check++; }
				if(&wordSearch($requiredWord, 'author') == 2){ $check++; }

				if($check){
					$stop++;
					last;
				}
				else {
					$check = 0;
				}
			}
		}
		$stop++ if($queryWords[2]{'t'} and not $stop and (&wordSearch(@{$queryWords[2]{'t'}}, 'title')));
		$stop++ if($queryWords[2]{'d'} and not $stop and (&wordSearch(@{$queryWords[2]{'d'}}, 'description')));
		$stop++ if($queryWords[2]{'u'} and not $stop and (&wordSearch(@{$queryWords[2]{'u'}}, 'url')));
		$stop++ if($queryWords[2]{'k'} and not $stop and (&wordSearch(@{$queryWords[2]{'k'}}, 'keywords')));
		$stop++ if($queryWords[2]{'a'} and not $stop and (&wordSearch(@{$queryWords[2]{'a'}}, 'author')));


		#If all required words are matched, and words have been matched
		if(not $stop and ( $matches{'title'} || $matches{'description'} || $matches{'url'} || $matches{'keywords'} || $matches{'author'})){
			$resultNumber++;
			$thekey = int($matches{'title'}*$config{'matchtitle'} + $matches{'description'}*$config{'matchdescription'} + $matches{'url'}*$config{'matchurl'} + $matches{'keywords'}*$config{'matchkeywords'} + $matches{'author'}*$config{'matchauthor'}) . $filler;
			%{$unsortedResults{$thekey}} = %entryFields;
			$filler--;
		}

		#Reset the match values
		$matches{'title'} = 0;
		$matches{'description'} = 0;
		$matches{'url'} = 0;
		$matches{'keywords'} = 0;
  		$matches{'author'} = 0;
	}
}

#Sort by importance and push everything to @results
foreach (sort {$b <=> $a} keys %unsortedResults){
	push(@results, $unsortedResults{$_});
}

&closeDatabase;

#######################
#  Print the results  ##################################################################################################
#######################

#if some guy is being a troublemaker. Meaning, they have tried to view a search results page that does not exist :o)
$query{'page'} = 1 if $query{'page'} < 1;
if($resultNumber <= 0){
	$query{'page'} = 1;
}
else {
	if( (($query{'page'} - 1) * $query{'perpage'}) >= $resultNumber){
		if( ($resultNumber / $query{'perpage'}) > int($resultNumber / $query{'perpage'})){
			$query{'page'} = (int($resultNumber / $query{'perpage'}) + 1);
		}
		else {
			$query{'page'} = int($resultNumber / $query{'perpage'});
		}
	}
}

#Find out the total number of pages that have the results
if( ($resultNumber / $query{'perpage'}) > int($resultNumber / $query{'perpage'})){
	$pagesOfResults =  (int($resultNumber / $query{'perpage'}) + 1);
}
else {
	$pagesOfResults = int($resultNumber / $query{'perpage'});
}


#Define the URLs for going through the pages that contain the search results, and 'true' and 'false' for $isNextPage and $isPreviousPage---------------------------------------------
if(($query{'page'} - 1) >= 1){
	$previousPageUrl = $urlNoPage . '&page=' . ($query{'page'} - 1);
	$isPreviousPage = 'true';
}
else {
	$previousPageUrl = "javascript:alert('You are at the beginning of the search results!')";
	$isPreviousPage = 'false';
}

if( ((($query{'page'} - 1) * $query{'perpage'}) + $query{'perpage'}) < $resultNumber){
	$nextPageUrl = $urlNoPage . '&page=' . ($query{'page'} + 1);
	$isNextPage = 'true';
}
else {
	$nextPageUrl = "javascript:alert('You are at the end of your search results.')";
	$isNextPage = 'false';
}



#divide and print the results into chunks that will be displayed on multiple pages--------------------------------------
#if($config{'resulttemplate'} eq 'true'){ 	#If you want to use the result template
	open(RESULTTEMPLATE, "html/resulttemplate.html") or &cgidie(&errorMsg("Error code 004: Could not open the result template (html/resulttemplate.html"), &reportError("004"), &backButton);
	@resultTemplate = <RESULTTEMPLATE>;
	close RESULTTEMPLATE;
#}

#Add all results that are within a spacific range to $searchResults
for($i = ($query{'perpage'} * ($query{'page'} - 1)); $i < @results && $i < ($query{'page'} * $query{'perpage'}); $i++){
	#if($config{'resulttemplate'} eq 'true'){	#If you want to use result template
		my @template = @resultTemplate;

		foreach (@template){	#Replace certain words from each line with the corresponding words from the results
			s/_resultnumber_/$i + 1/eig;
			s/_type_/$results[$i]{'type'}/ig;
			s/_date_/$results[$i]{'date'}/ig;
			s/_title_/$results[$i]{'title'}/ig;
			s/_description_/$results[$i]{'description'}/ig;
			s/_url_/$results[$i]{'url'}/ig;
			s/_keywords_/$results[$i]{'keywords'}/ig;
			s/_author_/$results[$i]{'author'}/ig;

			foreach $regExMatch (/(\s(?:href|src)=".*?")/gi){
				$originalRegExMatch = $regExMatch;
				$regExMatch =~ s/\xBB|\xC9//g;
				s/\Q$originalRegExMatch\E/$regExMatch/;
			}

			$_ = &addStyleWordTags($_) if($query{'stylewords'} eq 'true');
			$searchResults .= $_; #Add to the search results that will be printed
		}
	#}
	#else {	#If you want predefined results
	#	if($query{'stylewords'} eq 'true'){
	#		$results[$i]{'title'} = &addStyleWordTags($results[$i]{'title'});
	#		$results[$i]{'description'} = &addStyleWordTags($results[$i]{'description'});
	#		$results[$i]{'url'} = &addStyleWordTags($results[$i]{'url'});
	#		$results[$i]{'keywords'} = &addStyleWordTags($results[$i]{'keywords'});
	#		$results[$i]{'author'} = &addStyleWordTags($results[$i]{'author'});
	#	}
	#
	#	$searchResults .= "<br>\n<div class=\"resultTitle\"><span class=\"resultNumber\">" . ($i + 1) . ". </span><a href=\"" . &stripTags($results[$i]{'url'}) . "\">$results[$i]{'title'}</a><span class=\"date\">$results[$i]{'date'}</span></div>\n";
	#	$searchResults .= "<div class=\"resultDescription\">$results[$i]{'description'}</div>\n";
	#	$searchResults .= "<div class=\"resultUrl\">" . $results[$i]{'url'} . "</div>\n";
	#	$searchResults .= "<div class=\"resultKeywords\">$results[$i]{'keywords'}</div>\n";
	#	$searchResults .= "<div class=\"resultAuthor\">$results[$i]{'author'}</div>\n\n";
	#}
}

if($resultNumber and $i){ $searchResults .= "&nbsp;<br>\n"; }	#Print a new line break at the end of the results.
if($config{'generatenav'} eq 'true'){
	if(not $resultNumber){
		$searchResults .= qq`<div class="noMatches">Sorry, no matches</div>\n`;
	}
	else {
		if($i >= $resultNumber){
			$searchResults .= "<div class=\"endOfResults\">End of Results</div>\n";
		}
		#Print jump links on the bottom (previous page/next page)
		if($i < $resultNumber || ($query{'page'} - 1)){
			$searchResults .= "<div align=\"center\" class=\"pageJump\">";

			#Previous page link
				if(($query{'page'} - 1)){ $searchResults .= "<a href=\"" . $previousPageUrl . "\">Previous page</a>";}
			#Separator between the links
				if($i < $resultNumber && ($query{'page'} - 1)){$searchResults .= "&nbsp;&nbsp;|&nbsp;&nbsp;";}
			#Next page link
				if($i < $resultNumber){$searchResults .= "<a href=\"" . $nextPageUrl . "\">Next page</a>";}

			$searchResults .= "</div>\n\n";
		}
	}
}

#Add the number of results, the type of search, and the search query to queryrecord.txt
if($config{'queryrecord'} eq 'true' and lc $query !~ /&page=/i){
	open(QUERYRECORD, '>>queryrecord.txt') or &cgidie(&errorMsg("Error code 005: Was not able to add to queryrecord.txt</div>"), &reportError("005"), &backButton);
	#print QUERYRECORD sprintf("%-25s%-20s%-50s%-10s%-10s%s\n", "$month/$dayOfMonth/$year $hour:$minute:$second", $ENV{'REMOTE_ADDR'}, substr($ENV{'HTTP_USER_AGENT'}, 0, 45), $resultNumber, $query{'type'}, $query{'string'});
	print QUERYRECORD "$month/$dayOfMonth/$year $hour:$minute:$second", "\t\t", $ENV{'REMOTE_ADDR'}, "\t\t", $ENV{'HTTP_USER_AGENT'}, "\t\t", $resultNumber, "\t\t", $query{'type'}, "\t\t", $query{'string'}, "\n";
	close(QUERYRECORD);
}

#Print the footer for the Results page-----------------------------------------------------------------------------------
open(SEARCHRESULTS, 'html/searchresults.html') or &cgidie(&errorMsg("Error code 006: Could not open the search results file (html/searchresults.html)"), &reportError("006"), &backButton);
while(<SEARCHRESULTS>){
	s/_totalentries_/$entryNumber/ig;
	s/_totalresults_/$resultNumber/ig;
	s/_nextpageurl_/$nextPageUrl/ig;
	s/_previouspageurl_/$previousPageUrl/ig;
	s/_nextpage_/$isNextPage/ig;
	s/_previouspage_/$isPreviousPage/ig;
	s/_stylewords_/$query{'stylewords'}/ig;
	s/_perpage_/$query{'perpage'}/ig;
	s/_currentpage_/$query{'page'}/ig;
	s/_searchqueryENCODED_/$hexQuery{'string'}/ig;
	s/_searchqueryTEXT_/$query{'string'}/ig;
	s/_searchqueryHTML_/$htmlQuery{'string'}/ig;
	s/_searchtype_/$query{'type'}/ig;
	s/_searchresults_/$searchResults/ig;
	print;
}
close(SEARCHRESULTS);






##################
#   Subroutines   ########################################################################################################
##################


sub cgidie {
	print join('', @_);
	exit;
	#return ((wantarray)? ('installed' => 'false')) : 0;
}

sub trim {
	my $string = shift;
	return $string if not $string;	
	$string =~ s/\s+/ /g;
	$string =~ s/^ //;
	$string =~ s/ $//;
	return $string;
}

sub addStyleWordTags {
	my $string = shift;
	$string =~ s/$endStyle+/$endStyle/g;
	$string =~ s/$startStyle+/$startStyle/g;
	$string =~ s/$endStyle/<\/span>/g;
	$string =~ s/$startStyle/<span class="matchedWord">/g;
	return $string;
}

sub stripTags {
	my $string = shift;
	$string =~ s/<script(.|\n)*?\/script>//gim;
	$string =~ s/<style(.|\n)*?\/style>//gim;
	$string =~ s/<!--(.|\n)*?-->//gim;
	$string =~ s/<(.|\n)*?>//gim;
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

sub wordSearch {
	#Returns 2 if all words were matched
	#Returns 1 if one or more were matched but not all
	#Returns 0 if none were matched

	my $section = pop(@_);
	my @words = @_;
	my @matched = ();
	my $matched = 0;
	my $word = '';

	foreach $word (@words){
		$word =~ s/(\^|\$|\+|\.|\||\(|\)|\{|\}|\[|\])/\\$1/g;
		$word =~ s/\?/\\w/g;
		$word =~ s/\*/\\w*?/g;

		if($entryFields{$section} =~ m/$word/i){
			my($mymatched) = 0;
			@matched = ();
			@matched = ($entryFields{$section} =~ m/\b($word)\b/ig);
			$matches{$section} += 3 * scalar(@matched);
			if($query{'stylewords'} eq 'true'){
				$entryFields{$section} =~ s/\b($word)\b/$startStyle$1$endStyle/ig;
			}
			$mymatched = 1 if(@matched);


			if(length($word) >= int($config{'wordsize'}) ){
				if($word =~ m/ /){
					@matched = ();
					@matched = ($entryFields{$section} =~ m/($word)/ig);
					$matches{$section} += 2.5 * scalar(@matched);
					if($query{'stylewords'} eq 'true'){
						$entryFields{$section} =~ s/($word)/$startStyle$1$endStyle/ig;
					}
					if(@matched){
						$mymatched ||= 1;
					}
				}
				else {
					@matched = ();
					@matched = ($entryFields{$section} =~ m/($word)/ig);
					$matches{$section} += (@matched);
					if($query{'stylewords'} eq 'true'){
						$entryFields{$section} =~ s/($word)/$startStyle$1$endStyle/ig;
					}
					if(@matched){
						$mymatched ||= 1;
					}
				}
			}
			$matched += $mymatched;
		}
	}

	#Return the results
	if( $matched == scalar(@words) ){
		return 2;
	}
	elsif($matched){
		return 1;
	}
	else {
		return 0;
	}

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

sub syntax {
	my $section = pop(@_);
	my $letter = substr($section, 0, 1);
	my (@matches, @quoted) = ();
	my $found = '';
	my $match = '';

	if($section ne 'X'){
		@matches = ($query{'string'} =~ m/(?:$letter|$section)\((.*?)\)/ig);
		$found = join(" ", @matches);
	}
	else {
		$found = $query{'string'};
	}

	@quoted = ($found =~ m/\+"(.+?)"/ig );  #eg: +"Search Query"
	foreach $match (@quoted){
		$found =~ s/(\+".+?")//g;
		$match = &trim($match);
		push(@{$queryWords[1]{$letter}}, $match);
	}
	@quoted = ($found =~ m/-"(.+?)"/ig );  #eg: -"Search Query"
	foreach $match (@quoted){
		$found =~ s/(-".+?")//g;
		$match = &trim($match);
		push(@{$queryWords[2]{$letter}}, $match);
	}
	@quoted = ($found =~ m/"(.+?)"/ig );  #eg: "Search Query"
	foreach $match (@quoted){
		$found =~ s/(".+?")//g;
		$match = &trim($match);
		push(@{$queryWords[0]{$letter}}, $match);
	}
	$found = &trim($found);

	push(@{$queryWords[0]{$letter}}, split(/ /, $found));
	if($section ne "X"){
		$query{'string'} =~ s/($letter|$section)\(.*?\)//gi;
	}
	else {
		$query{'string'} = $found;
	}
	$found = '';

	my $i = 0;
	while($i < scalar(@{$queryWords[0]{$letter}}) ){
		if( $queryWords[0]{$letter}[$i] =~ m/^-(?:\w|\?|\*)/ ){ #Remove words that begin with '-'
			$queryWords[0]{$letter}[$i] =~ s/^-//;
			push(@{$queryWords[2]{$letter}}, $queryWords[0]{$letter}[$i]);
			splice(@{$queryWords[0]{$letter}}, $i, 1);
		}
		elsif( $queryWords[0]{$letter}[$i] =~ m/^\+(?:\w|\?|\*)/ ){ #Place words that begin with '+'
			$queryWords[0]{$letter}[$i] =~ s/^\+//;
			push(@{$queryWords[1]{$letter}}, $queryWords[0]{$letter}[$i]);
			splice(@{$queryWords[0]{$letter}}, $i, 1);
		}
		else {
			$i++;
		}
	}
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
