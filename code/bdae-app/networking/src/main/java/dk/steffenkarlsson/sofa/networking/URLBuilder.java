package dk.steffenkarlsson.sofa.networking;

import android.net.Uri;
import android.util.Pair;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by steffenkarlsson on 23/12/14.
 */
@SuppressWarnings("ALL")
public class URLBuilder {

    private String mSubdomain = "";
    private List<Pair<String, String>> mParameters = new ArrayList<>();

    public URLBuilder addApiVersion() {
        return subdomain("v1/");
    }

    public URLBuilder subdomain(String subdomain) {
        this.mSubdomain += subdomain;
        return this;
    }

    public URLBuilder addParameter(String key, String value) {
        mParameters.add(new Pair<String, String>(key, value));
        return this;
    }

    public String build(String baseUrl) {
        Uri.Builder builder = Uri.parse(baseUrl + mSubdomain).buildUpon();
        for (Pair<String, String> parameter : mParameters)
            builder.appendQueryParameter(parameter.first, parameter.second);

        return builder.build().toString();
    }

}