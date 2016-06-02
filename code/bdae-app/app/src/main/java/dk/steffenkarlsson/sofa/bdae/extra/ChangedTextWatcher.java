package dk.steffenkarlsson.sofa.bdae.extra;

import android.support.annotation.NonNull;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.util.Patterns;
import android.view.View;

import com.rengwuxian.materialedittext.MaterialEditText;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class ChangedTextWatcher implements TextWatcher {

    private static boolean isValidIPPort(String input) {
        if (!input.contains(":"))
            return false;

        String[] ipport = input.split(":");
        if (ipport.length == 0 || ipport.length == 1)
            return false;

        return Patterns.IP_ADDRESS.matcher(ipport[0]).matches() && TextUtils.isDigitsOnly(ipport[1]);
    }

    public static boolean emptyValidator(MaterialEditText editText, Editable s) {
        boolean isEmpty = TextUtils.isEmpty(s.toString());
        if (isEmpty)
            editText.setError("Required Field");
        return !isEmpty;
    }

    public static boolean ipPortValidator(MaterialEditText editText, Editable s) {
        boolean validated = false;
        if (TextUtils.isEmpty(s.toString()))
            editText.setError("Required Field");
        else {
            if (!isValidIPPort(s.toString()))
                editText.setError("Has to be a valid ip:port");
            else
                validated = true;
        }
        return validated;
    }

    public interface OnValidateListener {
        void onValidated(int index, boolean isValid, boolean hasChanged);
        boolean validate(MaterialEditText editText, Editable s);
    }

    private final MaterialEditText mEditText;
    private final int mIndex;
    private OnValidateListener mOnValidateListener;
    private String mCurrentText;

    public ChangedTextWatcher(MaterialEditText editText, int index, @NonNull  OnValidateListener onValidateListener) {
        this.mEditText = editText;
        this.mCurrentText = editText.getText().toString();
        this.mIndex = index;
        this.mOnValidateListener = onValidateListener;

        mEditText.setOnFocusChangeListener(new View.OnFocusChangeListener() {
            @Override
            public void onFocusChange(View v, boolean hasFocus) {
                if (!hasFocus) {
                    ChangedTextWatcher.this.mCurrentText = mEditText.getText().toString();
                }
            }
        });
    }

    @Override
    public void beforeTextChanged(CharSequence s, int start, int count, int after) {
    }

    @Override
    public void onTextChanged(CharSequence s, int start, int before, int count) {
    }

    @Override
    public void afterTextChanged(Editable s) {
        mOnValidateListener.onValidated(mIndex,
                mOnValidateListener.validate(mEditText, s),
                !mCurrentText.equals(s.toString()));
    }
}